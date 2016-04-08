#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1
from base64 import b16encode
from django.contrib.gis.geos import GEOSGeometry
from re import compile as re_compile

from base.tests import APITestBase
from image import models
from PIL import Image as PIL_Image
from image import exif_lib
from account.models import VD


class ImageTest(APITestBase):

    def test_string_representation(self):
        img_id = uuid1()
        img = models.Image(id=img_id)
        self.assertEqual(unicode(img), '%s.img' % b16encode(img_id.bytes))
        self.assertEqual(img.uuid, unicode(img))

    def test_save_and_retreive(self):
        img = models.Image()
        img.file = self.uploadImage('test.jpg')
        img.save()
        saved = models.Image.objects.first()

        self.assertEqual(saved, img)
        saved2 = models.Image.get_from_json('{"uuid": "%s", "content": null}' % img.uuid)
        self.assertEqual(saved2, img)
        saved3 = models.Image.get_from_json('{"uuid": "%s", "content": null, "note": {"uuid": null, "content": null}}' % img.uuid)
        self.assertEqual(saved3, img)
        with self.assertRaises(NotImplementedError):
            models.Image.get_from_json('{"uuid": null, "content": "%s"}' % img.content)

    def test_file_property(self):
        img = models.Image()
        img.file = self.uploadImage('test.jpg')
        img.save()
        saved = models.Image.objects.first()

        url = img.file.url
        self.assertEqual(img.content, url)
        regex = re_compile(r'^.*images/\d{4}/\d{1,2}/\d{1,2}/.+\.jpg$')
        self.assertNotEqual(regex.match(url), None)
        self.assertEqual(url.endswith('.jpg'), True)
        self.assertEqual(saved, img)
        self.assertEqual(saved.uuid, img.uuid)
        self.assertEqual(saved.file, img.file)
        self.assertEqual(saved.content, img.content)

        img2 = models.Image()
        img2.file = self.uploadImage('test.png')
        with self.assertRaises(NotImplementedError):
            img2.save()

    def test_id(self):
        id_640 = models.Image.compute_id_from_file('image/samples/test.jpg')
        id_256 = models.Image.compute_id_from_file('image/samples/test_256.jpg')
        id_480 = models.Image.compute_id_from_file('image/samples/test_480.jpg')
        #id_1200 = models.Image.compute_id_from_file('image/samples/test_1200.jpg')
        #id_org = models.Image.compute_id_from_file('image/samples/test_org.jpg')
        id2 = models.Image.compute_id_from_file('image/samples/no_exif_test.jpg')

        self.assertLessEqual(models.Image.hamming_distance(id_640, id_256), 0)
        self.assertLessEqual(models.Image.hamming_distance(id_640, id_480), 1)
        #self.assertLessEqual(models.Image.hamming_distance(id_640, id_1200), 0)
        #self.assertLessEqual(models.Image.hamming_distance(id_640, id_org), 2)
        self.assertGreater(models.Image.hamming_distance(id_640, id2), 10)  # distance = 59

    def test_gps_exif(self):
        exif = exif_lib.get_exif_data(PIL_Image.open('image/samples/gps_test.jpg'))
        lonLat = exif_lib.get_lon_lat(exif)
        point = GEOSGeometry('POINT(%f %f)' % lonLat)
        self.assertEqual(point.x, 127.103744)  # lon(경도)
        self.assertEqual(point.y, 37.399731)  # lat(위도)

        img = models.Image()
        img.file = self.uploadImage('gps_test.jpg')
        img.save()
        saved = models.Image.objects.first()

        self.assertEqual(img.lonLat, point)
        self.assertEqual(saved.lonLat, point)

    def test_no_exif(self):
        exif = exif_lib.get_exif_data(PIL_Image.open('image/samples/no_exif_test.jpg'))
        lonLat = exif_lib.get_lon_lat(exif)
        self.assertIsNone(lonLat[0])
        self.assertIsNone(lonLat[1])

        img = models.Image()
        img.file = self.uploadImage('no_exif_test.jpg')
        img.save()
        saved = models.Image.objects.first()

        self.assertEqual(img, saved)
        self.assertIsNone(img.lonLat)
        self.assertIsNone(saved.lonLat)


class RawFileTest(APITestBase):

    def test_string_representation(self):
        rf_id = uuid1()
        rf = models.RawFile(id=rf_id)
        self.assertEqual(unicode(rf), '%s.rf' % b16encode(rf_id.bytes))
        self.assertEqual(rf.uuid, unicode(rf))

    def test_save_and_retreive(self):
        rf = models.RawFile()
        rf.file = self.uploadFile('test.png')
        rf.save()
        saved = models.RawFile.objects.first()
        self.assertEqual(saved, rf)
        self.assertEqual(saved.file, rf.file)

    def test_file_property(self):
        rf = models.RawFile()
        rf.file = self.uploadFile('test.png')
        rf.save()
        saved = models.RawFile.objects.first()

        url = rf.file.url
        print(url)
        regex = re_compile(r'^.*rfs/\d{4}/\d{1,2}/\d{1,2}/.+$')
        self.assertNotEqual(regex.match(url), None)
        self.assertEqual(saved, rf)
        self.assertEqual(saved.uuid, rf.uuid)
        self.assertEqual(saved.file, rf.file)

    def test_vd_property(self):
        vd = VD(); vd.save()
        rf = models.RawFile()
        rf.file = self.uploadFile('test.png')
        rf.vd = vd
        rf.save()
        saved = models.RawFile.objects.first()
        self.assertNotEqual(rf.vd, None)
        self.assertEqual(saved, rf)
        self.assertEqual(saved.vd, rf.vd)

