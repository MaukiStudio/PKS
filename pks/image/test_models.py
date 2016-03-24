#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1
from base64 import b16encode
from django.test import TestCase
from django.core.files import File

from image import models


class ImageTest(TestCase):

    def test_string_representation(self):
        uuid_img = uuid1()
        img = models.Image(pk=uuid_img)
        self.assertEqual('%s.jpg' % b16encode(uuid_img.bytes), str(img))

    def test_save_and_retreive(self):
        img = models.Image(pk=uuid1())
        img.save()
        saved = models.Image.objects.first()
        self.assertEqual(img, saved)

    def test_file_property(self):
        img = models.Image(pk=uuid1())
        with open('image/test.jpg', 'rb') as f:
            img.file = File(f, name=str(img))
            img.save()
        saved = models.Image.objects.first()
        self.assertTrue(saved.file.url.endswith(str(img)))
