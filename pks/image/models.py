#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b16encode
from uuid import UUID
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from random import randrange

from imagehash import dhash
from PIL import Image as PIL_Image
from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE
from base.models import Content
from base.legacy import exif_lib
from base.legacy.urlnorm import norms as url_norms

RAW_FILE_PATH = 'rfs/%Y/%m/%d/'


class Image(Content):
    dhash = models.UUIDField(blank=True, null=True, default=None, db_index=True)
    lonLat = models.PointField(blank=True, null=True, default=None)

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
        return url_norms(raw_content.strip())

    def pre_save(self):
        ext = self.content.split('.')[-1]
        if ext.lower() not in ('jpg', 'jpeg'):
            raise NotImplementedError
        if not self.lonLat:
            # TODO : CacheManager 만들어서 file 값 할당하기
            file = None
            self.process_exif(file)

    def post_save(self):
        # file 을 바로 access 하지 못한 경우, Celery 에 작업 의뢰
        if not self.dhash:
            pass

    # Image's method
    @classmethod
    def compute_id_from_file(cls, file):
        pil = PIL_Image.open(file)
        d1 = dhash(pil)
        d2 = dhash(pil.transpose(PIL_Image.ROTATE_90))
        return UUID('%s%s' % (d1, d2))

    @classmethod
    def hamming_distance(cls, id1, id2):
        count, z = 0, id1.int ^ id2.int
        while z:
            count += 1
            z &= z - 1
        return count

    def process_exif(self, file):
        if not file:
            return
        exif = exif_lib.get_exif_data(PIL_Image.open(file))
        lonLat = exif_lib.get_lon_lat(exif)
        if lonLat[0] and lonLat[1]:
            point = GEOSGeometry('POINT(%f %f)' % lonLat)
            self.lonLat = point


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

