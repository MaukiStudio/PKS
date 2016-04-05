#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b16encode
from uuid import UUID
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from json import loads as json_loads

from imagehash import dhash
from PIL import Image as PIL_Image
from image import exif_lib


IMAGE_PATH = 'images'


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
        if self.file and not self.id:
            self.set_id()
        if self.file and not self.lonLat:
            self.process_exif()
        self.file.name = unicode(self)
        super(Image, self).save(*args, **kwargs)

    @property
    def uuid(self):
        return '%s.jpg' % b16encode(self.id.bytes)

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
        return None

