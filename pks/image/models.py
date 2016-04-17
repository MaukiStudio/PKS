#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b16encode
from uuid import UUID
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from random import randrange
from json import loads as json_loads

from imagehash import dhash
from PIL import Image as PIL_Image, ImageOps as PIL_ImageOps
from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE
from base.models import Content
from base.legacy import exif_lib
from base.legacy.urlnorm import norms as url_norms
from pks.settings import SERVER_HOST

RAW_FILE_PATH = 'rfs/%Y/%m/%d/'


class Image(Content):
    dhash = models.UUIDField(blank=True, null=True, default=None, db_index=True)
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)

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
        ext = self.content.split('.')[-1]
        if ext.lower() not in ('jpg', 'jpeg'):
            raise NotImplementedError
        if self.is_accessed:
            pil = PIL_Image.open(self.path_accessed)
            if not self.lonLat:
                self.lonLat = self.process_exif(pil)
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
        if not file:
            return None
        exif = exif_lib.get_exif_data(pil)
        lonLat = exif_lib.get_lon_lat(exif)
        if lonLat[0] and lonLat[1]:
            return GEOSGeometry('POINT(%f %f)' % lonLat)
        return None

    def summarize_force(self, accessed=None):
        if not accessed:
            accessed = PIL_Image.open(self.path_accessed)
        thumb = PIL_ImageOps.fit(accessed, (300, 300), PIL_Image.ANTIALIAS)
        thumb.save(self.path_summarized)

    @classmethod
    def hamming_distance(cls, id1, id2):
        count, z = 0, id1.int ^ id2.int
        while z:
            count += 1
            z &= z - 1
        return count


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
        hstr = hex((timestamp << 8*8) | (vd_id << 2*8) | randrange(0, 65536))[2:-1]
        return UUID(hstr.rjust(32, b'0'))

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
