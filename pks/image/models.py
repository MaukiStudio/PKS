#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b16encode
from uuid import UUID
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry

from imagehash import dhash
from PIL import Image as PIL_Image
from image import exif_lib


IMAGE_PATH = 'images'


class Image(models.Model):
    uuid = models.UUIDField(primary_key=True, default=None)
    file = models.ImageField(blank=True, null=True, default=None, upload_to=IMAGE_PATH)
    lonLat = models.PointField(blank=True, null=True, default=None)

    @classmethod
    def compute_uuid_from_file(cls, file):
        pil = PIL_Image.open(file)
        d1 = dhash(pil)
        d2 = dhash(pil.transpose(PIL_Image.ROTATE_90))
        return UUID('%s%s' % (d1, d2))

    @classmethod
    def hamming_distance(cls, uuid1, uuid2):
        count, z = 0, uuid1.int ^ uuid2.int
        while z:
            count += 1
            z &= z - 1
        return count

    def set_uuid(self):
        self.file.open()
        self.uuid = Image.compute_uuid_from_file(self.file)
        self.file.open()
        return self.uuid

    def process_exif(self):
        self.file.open()
        exif = exif_lib.get_exif_data(PIL_Image.open(self.file))
        self.file.open()
        lonLat = exif_lib.get_lat_lon(exif)
        if lonLat[0] and lonLat[1]:
            point = GEOSGeometry('POINT(%f %f)' % lonLat)
            self.lonLat = point

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.set_uuid()
        self.process_exif()
        self.file.name = str(self)
        super(Image, self).save(*args, **kwargs)

    def __str__(self):
        return '%s.jpg' % b16encode(self.uuid.bytes)
