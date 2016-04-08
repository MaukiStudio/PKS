#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b16encode
from uuid import UUID
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from json import loads as json_loads
from random import randrange

from imagehash import dhash
from PIL import Image as PIL_Image
from image import exif_lib
from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE

IMAGE_PATH = 'images/%Y/%m/%d/'
RAW_FILE_PATH = 'rfs/%Y/%m/%d/'


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

        # TODO : mhash 구현. 장고 Celery 로 처리

        # 저장
        self.id = _id
        self.file.name = '%s_%s' % (self.uuid, self.file.name)
        super(RawFile, self).save(*args, **kwargs)


class Image(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    file = models.ImageField(blank=True, null=True, default=None, upload_to=IMAGE_PATH)
    lonLat = models.PointField(blank=True, null=True, default=None)

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

    def set_id(self):
        self.file.open()
        self.id = Image.compute_id_from_file(self.file)
        self.file.open()

    def process_exif(self):
        self.file.open()
        exif = exif_lib.get_exif_data(PIL_Image.open(self.file))
        self.file.open()
        lonLat = exif_lib.get_lon_lat(exif)
        if lonLat[0] and lonLat[1]:
            point = GEOSGeometry('POINT(%f %f)' % lonLat)
            self.lonLat = point

    def save(self, *args, **kwargs):
        if not self.file.url.endswith('.jpg'):
            raise NotImplementedError
        if not self.id and self.file:
            self.set_id()
        if not self.lonLat and self.file:
            self.process_exif()
        #self.file.name = self.accessed
        super(Image, self).save(*args, **kwargs)

    @property
    def uuid(self):
        return '%s.img' % b16encode(self.id.bytes)

    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json =json_loads(json)
        result = None
        if 'uuid' in json and json['uuid']:
            _id = UUID(json['uuid'].split('.')[0])
            result = cls.objects.get(id=_id)
        elif 'content' in json and json['content']:
            raise NotImplementedError
        return result

    def __unicode__(self):
        return self.uuid

    @property
    def content(self):
        return self.file.url

    @property
    def accessed(self):
        return '%s.jpg' % self.uuid
