#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1
from base64 import b16encode
from django.test import TestCase
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile

from image import models


class ImageTest(TestCase):

    def test_string_representation(self):
        uuid_img = uuid1()
        img = models.Image(pk=uuid_img)
        self.assertEqual('%s.jpg' % b16encode(uuid_img.bytes), str(img))

    def test_file_property(self):
        img = models.Image()
        with open('image/test.jpg', 'rb') as f:
            ff = File(f)
            img.file = InMemoryUploadedFile(ff, None, 'test.jpg', 'image/jpeg', ff.size, None, None)
            img.save()
        saved = models.Image.objects.first()
        self.assertEqual(saved, img)
        self.assertNotEqual(saved.file.url.index(str(img).split('.')[0]), 0)

    def test_uuid(self):
        uuid = models.Image.compute_uuid_from_file('image/test.jpg')
        uuid_256 = models.Image.compute_uuid_from_file('image/test_256.jpg')
        uuid_1200 = models.Image.compute_uuid_from_file('image/test_1200.jpg')

        self.assertEqual(uuid, uuid_256)
        self.assertEqual(uuid, uuid_1200)
