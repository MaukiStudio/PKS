#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from os import remove
from base64 import b16encode
from uuid import UUID
from PIL import Image as PIL
from django.contrib.gis.db import models

from imagehash import dhash


IMAGE_PATH = 'images'


class Image(models.Model):
    uuid = models.UUIDField(primary_key=True, default=None)
    file = models.ImageField(blank=True, null=True, default=None, upload_to=IMAGE_PATH)

    @classmethod
    def compute_uuid_from_file(cls, file):
        pil = PIL.open(file)
        d1 = dhash(pil)
        d2 = dhash(pil.transpose(PIL.ROTATE_90))
        return UUID('%s%s' % (d1, d2))

    def set_uuid(self):
        self.uuid = Image.compute_uuid_from_file(self.file)
        return self.uuid

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.set_uuid()
        self.file.name = str(self)
        super(Image, self).save(*args, **kwargs)

    def __str__(self):
        return '%s.jpg' % b16encode(self.uuid.bytes)
