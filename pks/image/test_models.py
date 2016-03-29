#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1
from base64 import b16encode
from django.contrib.gis.geos import GEOSGeometry

from base.tests import APITestBase
from image import models
from PIL import Image as PIL_Image
from image import exif_lib


class ImageTest(APITestBase):

    def test_string_representation(self):
        uuid_img = uuid1()
        img = models.Image(pk=uuid_img)
        self.assertEqual('%s.jpg' % b16encode(uuid_img.bytes), str(img))

    def test_file_property(self):
        img = models.Image()
        img.file = self.uploadImage('test.jpg')
        img.save()
        saved = models.Image.objects.first()
        self.assertEqual(saved, img)
        self.assertNotEqual(saved.file.url.index(str(img).split('.')[0]), 0)

    def __skip__test_uuid(self):
        uuid = models.Image.compute_uuid_from_file('image/samples/test.jpg')
        uuid_256 = models.Image.compute_uuid_from_file('image/samples/test_256.jpg')
        uuid_480 = models.Image.compute_uuid_from_file('image/samples/test_480.jpg')
        uuid_1200 = models.Image.compute_uuid_from_file('image/samples/test_1200.jpg')
        uuid_org = models.Image.compute_uuid_from_file('image/samples/test_org.jpg')
        uuid2 = models.Image.compute_uuid_from_file('image/samples/test2.jpg')

        self.assertLessEqual(models.Image.hamming_distance(uuid, uuid_256), 0)
        self.assertLessEqual(models.Image.hamming_distance(uuid, uuid_480), 1)
        self.assertLessEqual(models.Image.hamming_distance(uuid, uuid_1200), 0)
        self.assertLessEqual(models.Image.hamming_distance(uuid, uuid_org), 2)
        self.assertGreater(models.Image.hamming_distance(uuid, uuid2), 10)

    def test_gps_exif(self):
        exif = exif_lib.get_exif_data(PIL_Image.open('image/samples/gps_test.jpg'))
        lonLat = exif_lib.get_lat_lon(exif)
        point = GEOSGeometry('POINT(%f %f)' % lonLat)
        print(point)

        img = models.Image()
        img.file = self.uploadImage('gps_test.jpg')
        img.save()
        saved = models.Image.objects.first()

        self.assertEqual(point, img.lonLat)
        self.assertEqual(img.lonLat, saved.lonLat)

    def test_no_exif(self):
        exif = exif_lib.get_exif_data(PIL_Image.open('image/samples/no_exif_test.jpg'))
        lonLat = exif_lib.get_lat_lon(exif)
        self.assertIsNone(lonLat[0])
        self.assertIsNone(lonLat[1])

        img = models.Image()
        img.file = self.uploadImage('no_exif_test.jpg')
        img.save()
        saved = models.Image.objects.first()

        self.assertEqual(img, saved)
        self.assertIsNone(img.lonLat)
        self.assertIsNone(saved.lonLat)
