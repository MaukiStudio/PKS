#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b16encode
from uuid import UUID
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from json import loads as json_loads
from rest_framework import status

from imagehash import dhash
from PIL import Image as PIL_Image, ImageOps as PIL_ImageOps
from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE, get_uuid_from_ts_vd
from base.models import Content
from base.legacy import exif_lib
from base.legacy.urlnorm import norms as url_norms
from pks.settings import SERVER_HOST
from requests import get as requests_get
from pathlib2 import Path


RAW_FILE_PATH = 'rfs/%Y/%m/%d/'


class Image(Content):
    dhash = models.UUIDField(blank=True, null=True, default=None, db_index=True)
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)
    timestamp = models.BigIntegerField(blank=True, null=True, default=None)

    # MUST override
    @property
    def contentType(self):
        return 'img'

    @property
    def accessedType(self):
        return 'jpg'

    # CAN override
    @classmethod
    def normalize_content(cls, raw_content):
        url = url_norms(raw_content.strip())
        if not url.startswith('http'):
            url = '%s%s' % (SERVER_HOST, url)
        return url

    def pre_save(self):
        if self.is_accessed:
            pil = self.content_accessed
            if not self.lonLat or not self.timestamp:
                lonLat, timestamp = self.process_exif(pil)
                self.lonLat = self.lonLat or lonLat
                self.timestamp = self.timestamp or timestamp
            if not self.dhash:
                self.dhash = self.compute_id_from_file(pil)
            self.summarize(pil)


    def post_save(self):
        # TODO : file 을 바로 access 하지 못한 경우, Celery 에 작업 의뢰
        if not self.dhash:
            pass

    @property
    def json(self):
        if self.timestamp:
            if self.note:
                return dict(uuid=self.uuid, content=self.content, note=self.note.json, timestamp=self.timestamp, summary=self.url_summarized)
            else:
                return dict(uuid=self.uuid, content=self.content, timestamp=self.timestamp, summary=self.url_summarized)
        else:
            if self.note:
                return dict(uuid=self.uuid, content=self.content, note=self.note.json, summary=self.url_summarized)
            else:
                return dict(uuid=self.uuid, content=self.content, summary=self.url_summarized)

    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        self.note = None

    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json = json_loads(json)
        result = super(Image, cls).get_from_json(json)
        if result and 'note' in json and json['note']:
            from content.models import ImageNote
            result.note = ImageNote.get_from_json(json['note'])
        return result

    # Image's method
    @classmethod
    def compute_id_from_file(cls, pil):
        d1 = dhash(pil)
        d2 = dhash(pil.transpose(PIL_Image.ROTATE_90))
        return UUID('%s%s' % (d1, d2))

    @classmethod
    def process_exif(cls, pil):
        result = [None, None]
        if not pil:
            return result
        try:
            exif = exif_lib.get_exif_data(pil)
            lonLat = exif_lib.get_lon_lat(exif)
            if lonLat and lonLat[0] and lonLat[1]:
                result[0] = GEOSGeometry('POINT(%f %f)' % lonLat)
            timestamp = exif_lib.get_timestamp(exif)
            if timestamp:
                result[1] = timestamp
        except AttributeError:
            pass
        return result

    def summarize_force(self, accessed=None):
        if not accessed:
            accessed = self.content_accessed
        if accessed:
            thumb = PIL_ImageOps.fit(accessed, (300, 300), PIL_Image.ANTIALIAS).convert('RGB')
            thumb.save(self.path_summarized)

    @classmethod
    def hamming_distance(cls, id1, id2):
        count, z = 0, id1.int ^ id2.int
        while z:
            count += 1
            z &= z - 1
        return count

    @property
    def content_accessed(self):
        img = None
        try:
            img = PIL_Image.open(self.path_accessed)
        except IOError:
            pass
        return img

    def access_force(self, timeout=1):
        headers = {'user-agent': 'Chrome'}
        r = requests_get(self.url_for_access, headers=headers, timeout=timeout)
        if r.status_code not in (status.HTTP_200_OK,):
            print('Access failed : %s' % self.url_for_access)

        file = Path(self.path_accessed)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        summary = Path(self.path_summarized)
        if not Path(self.path_summarized).parent.exists():
            summary.parent.mkdir(parents=True)
        file.write_bytes(r.content)


class RawFile(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    file = models.FileField(blank=True, null=True, default=None, upload_to=RAW_FILE_PATH)
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='rfs')
    mhash = models.UUIDField(blank=True, null=True, default=None, db_index=True)

    @property
    def uuid(self):
        return '%s.rf' % b16encode(self.id.bytes)

    def __unicode__(self):
        return self.uuid

    def _id(self, timestamp):
        vd_id = self.vd_id or 0
        return get_uuid_from_ts_vd(timestamp, vd_id)

    @property
    def timestamp(self):
        return (int(self.id) >> 8*8) & BIT_ON_8_BYTE

    def save(self, *args, **kwargs):
        # id/file 처리
        if not self.file:
            raise AssertionError
        timestamp = kwargs.pop('timestamp', get_timestamp())
        _id = self._id(timestamp)
        if self.id and self.id != _id:
            raise NotImplementedError

        # TODO : mhash 구현. 장고 Celery 에 작업 의뢰

        # 저장
        self.id = _id
        self.file.name = '%s_%s' % (self.uuid, self.file.name)
        super(RawFile, self).save(*args, **kwargs)

        # 이미지인 경우 바로 캐시 처리
        ext = self.file.name.split('.')[-1]
        if ext.lower() in ('jpg', 'jpeg'):
            img = Image(content=self.file.url)
            img.content = img.normalize_content(img.content)
            if not img.content.startswith('http'):
                raise ValueError('Invalid image URL')
            img.id = img._id
            img.access_local(self.file.path)
