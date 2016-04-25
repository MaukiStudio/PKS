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
from base.legacy import exif_lib
from account.models import VD
from base.utils import get_timestamp
from content.models import ImageNote


class ImageTest(APITestBase):

    def test_string_representation(self):
        img = models.Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()
        self.assertEqual(unicode(img), img.content)
        self.assertEqual(img.uuid, '%s.img' % b16encode(img.id.bytes))

    def test_save_and_retreive(self):
        img = models.Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()
        saved = models.Image.objects.first()

        self.assertEqual(saved, img)
        saved2 = models.Image.get_from_json('{"uuid": "%s", "content": null}' % img.uuid)
        self.assertEqual(saved2, img)
        saved3 = models.Image.get_from_json('{"uuid": "%s", "content": null, "note": {"uuid": null, "content": null}}' % img.uuid)
        self.assertEqual(saved3, img)
        saved4 = models.Image.get_from_json('{"uuid": null, "content": "%s"}' % img.content)
        self.assertEqual(saved4, img)

    def test_content_property(self):
        img = models.Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()
        saved = models.Image.objects.first()

        url = test_data
        self.assertEqual(img.content, url)
        self.assertEqual(saved, img)
        self.assertEqual(saved.content, img.content)

        img2 = models.Image()
        img2.content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.png'
        img2.save()
        self.assertNotEqual(img2, img)

    def test_id(self):
        id_640 = models.Image.compute_id_from_file(PIL_Image.open('image/samples/test.jpg'))
        id_256 = models.Image.compute_id_from_file(PIL_Image.open('image/samples/test_256.jpg'))
        id_480 = models.Image.compute_id_from_file(PIL_Image.open('image/samples/test_480.jpg'))
        #id_1200 = models.Image.compute_id_from_file(PIL_Image.open('image/samples/test_1200.jpg'))
        #id_org = models.Image.compute_id_from_file(PIL_Image.open('image/samples/test_org.jpg'))
        id2 = models.Image.compute_id_from_file(PIL_Image.open('image/samples/no_exif_test.jpg'))

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

        rf = models.RawFile()
        rf.file = self.uploadFile('gps_test.jpg')
        rf.save()

        img = models.Image()
        img.content = rf.file.url
        img.save()
        saved = models.Image.objects.first()

        self.assertEqual(img.lonLat, point)
        self.assertEqual(saved.lonLat, point)

    def test_no_exif(self):
        exif = exif_lib.get_exif_data(PIL_Image.open('image/samples/no_exif_test.jpg'))
        lonLat = exif_lib.get_lon_lat(exif)
        self.assertIsNone(lonLat[0])
        self.assertIsNone(lonLat[1])

        rf = models.RawFile()
        rf.file = self.uploadFile('no_exif_test.jpg')
        rf.save()

        img = models.Image()
        img.content = rf.file.url
        img.save()
        saved = models.Image.objects.first()

        self.assertEqual(img.lonLat, None)
        self.assertEqual(saved, img)
        self.assertEqual(saved.lonLat, None)

    def test_dhash(self):
        rf = models.RawFile()
        rf.file = self.uploadFile('test.jpg')
        rf.save()
        rf2 = models.RawFile()
        rf2.file = self.uploadFile('test_256.jpg')
        rf2.save()

        img = models.Image()
        img.content = rf.file.url
        img.save()
        img2 = models.Image()
        img2.content = rf2.file.url
        img2.save()

        self.assertNotEqual(img.dhash, None)
        self.assertNotEqual(img2.dhash, None)
        self.assertEqual(img.dhash, img2.dhash)

    def test_access_methods(self):
        img = models.Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()

        img.access()
        self.assertValidLocalFile(img.path_accessed)
        self.assertValidInternetUrl(img.url_accessed)

    def test_summarize_methods(self):
        img = models.Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()

        img.summarize()
        self.assertValidLocalFile(img.path_summarized)
        self.assertValidInternetUrl(img.url_summarized)

    def test_json(self):
        img = models.Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()
        img.summarize()

        self.assertIn('uuid', img.json)
        self.assertIn('content', img.json)
        self.assertNotIn('note', img.json)
        self.assertNotIn('timestamp', img.json)
        self.assertIn('summary', img.json)

        img.timestamp = get_timestamp()
        inote = ImageNote(content='img note')
        inote.save()
        img.note = inote

        self.assertIn('uuid', img.json)
        self.assertIn('content', img.json)
        self.assertIn('note', img.json)
        self.assertIn('timestamp', img.json)
        self.assertIn('summary', img.json)

        self.assertIn('uuid', img.json['note'])
        self.assertIn('content', img.json['note'])
        self.assertNotIn('timestamp', img.json['note'])

        inote.timestamp = get_timestamp()
        self.assertIn('uuid', img.json['note'])
        self.assertIn('content', img.json['note'])
        self.assertIn('timestamp', img.json['note'])

        saved = models.Image.get_from_json(img.json)
        self.assertEqual(saved, img)
        self.assertEqual(saved.note, img.note)


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

    def test_image_cache(self):
        rf = models.RawFile()
        rf.file = self.uploadFile('test.jpg')
        rf.save()

        img = models.Image(content=rf.file.url)
        img.content = img.normalize_content(img.content)
        img.id = img._id
        self.assertValidLocalFile(img.path_accessed)
        self.assertValidInternetUrl(img.url_accessed)

        img.save()
        self.assertValidInternetUrl(img.url_accessed)
        self.assertValidInternetUrl(img.url_summarized)
