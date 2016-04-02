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
        img_id = uuid1()
        img = models.Image(id=img_id)
        self.assertEqual(unicode(img), '%s.jpg' % b16encode(img_id.bytes))
        self.assertEqual(img.uuid, unicode(img))
        self.assertEqual(img.content, img.uuid)

    def test_save_and_retreive(self):
        img = models.Image()
        img.id = uuid1()
        img.save()
        saved = models.Image.objects.first()
        self.assertEqual(saved, img)

    def test_file_property(self):
        img = models.Image()
        img.file = self.uploadImage('test.jpg')
        img.save()
        saved = models.Image.objects.first()
        self.assertEqual(saved, img)
        self.assertNotEqual(saved.file.url.index(str(img).split('.')[0]), 0)

    def __skip__test_id(self):
        id_640 = models.Image.compute_id_from_file('image/samples/test.jpg')
        id_256 = models.Image.compute_id_from_file('image/samples/test_256.jpg')
        id_480 = models.Image.compute_id_from_file('image/samples/test_480.jpg')
        id_1200 = models.Image.compute_id_from_file('image/samples/test_1200.jpg')
        id_org = models.Image.compute_id_from_file('image/samples/test_org.jpg')
        id2 = models.Image.compute_id_from_file('image/samples/test2.jpg')

        self.assertLessEqual(models.Image.hamming_distance(id_640, id_256), 0)
        self.assertLessEqual(models.Image.hamming_distance(id_640, id_480), 1)
        self.assertLessEqual(models.Image.hamming_distance(id_640, id_1200), 0)
        self.assertLessEqual(models.Image.hamming_distance(id_640, id_org), 2)
        self.assertGreater(models.Image.hamming_distance(id_640, id2), 10)

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
