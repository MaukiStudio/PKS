#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1
from base64 import b16encode
from django.contrib.gis.geos import GEOSGeometry
from re import compile as re_compile

from base.tests import APITestBase
from image.models import Image, RawFile
from PIL import Image as PIL_Image
from base.legacy import exif_lib
from account.models import VD
from base.utils import get_timestamp
from content.models import ImageNote
from pks.settings import SERVER_HOST
from pathlib2 import Path


class ImageTest(APITestBase):

    def test_string_representation(self):
        img = Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()
        self.assertEqual(unicode(img), img.content)
        self.assertEqual(img.uuid, '%s.img' % b16encode(img.id.bytes))

    def test_save_and_retreive(self):
        img = Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()
        saved = Image.objects.first()

        self.assertEqual(saved, img)
        saved2 = Image.get_from_json('{"uuid": "%s", "content": null}' % img.uuid)
        self.assertEqual(saved2, img)
        saved3 = Image.get_from_json('{"uuid": "%s", "content": null, "note": {"uuid": null, "content": null}}' % img.uuid)
        self.assertEqual(saved3, img)
        saved4 = Image.get_from_json('{"uuid": null, "content": "%s"}' % img.content)
        self.assertEqual(saved4, img)

    def test_content_property(self):
        img = Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()
        saved = Image.objects.first()

        url = test_data
        self.assertEqual(img.content, url)
        self.assertEqual(saved, img)
        self.assertEqual(saved.content, img.content)

        img2 = Image()
        img2.content = 'http://static.naver.net/www/mobile/edit/2016/0407/mobile_17004159045.png'
        img2.save()
        img2.summarize()
        self.assertNotEqual(img2, img)

        img3 = Image()
        img3.content = 'http://static.naver.net/www/mobile/edit/2016/0407/mobile_17004159045.png'
        img3.save()
        img3.summarize()
        self.assertEqual(img3, img2)

    def test_phash_hamming_dist(self):
        id_640 = Image.compute_phash(PIL_Image.open('image/samples/test.jpg'))
        id_256 = Image.compute_phash(PIL_Image.open('image/samples/test_256.jpg'))
        id_480 = Image.compute_phash(PIL_Image.open('image/samples/test_480.jpg'))
        #id_1200 = Image.compute_phash(PIL_Image.open('image/samples/test_1200.jpg'))
        #id_org = Image.compute_phash(PIL_Image.open('image/samples/test_org.jpg'))
        id2 = Image.compute_phash(PIL_Image.open('image/samples/no_exif_test.jpg'))

        self.assertLessEqual(Image.hamming_distance(id_640, id_256), 2)
        self.assertLessEqual(Image.hamming_distance(id_640, id_480), 0)
        #self.assertLessEqual(Image.hamming_distance(id_640, id_1200), 0)
        #self.assertLessEqual(Image.hamming_distance(id_640, id_org), 0)
        self.assertGreater(Image.hamming_distance(id_640, id2), 10)  # distance = 58

    def test_task(self):
        _rf = RawFile()
        _rf.file = self.uploadFile('no_exif_test.jpg')
        _rf.save()
        img = _rf.img
        self.assertEqual(Image.objects.count(), 1)
        saved = Image.objects.first()

        img.task()
        self.assertEqual(img.similar, None)

        saved.task()
        self.assertEqual(saved.phash, img.phash)
        self.assertEqual(saved.similar, img.similar)

        _rf2 = RawFile()
        _rf2.file = self.uploadFile('test.jpg')
        _rf2.save()
        img2 = _rf2.img
        img2.task()
        self.assertEqual(img.similar, None)
        self.assertEqual(img2.similar, None)

        _rf3 = RawFile()
        _rf3.file = self.uploadFile('test_480.jpg')
        _rf3.save()
        img3 = _rf3.img
        img3.lonLat = None
        img3.timestamp = None
        #img3.save()
        self.assertEqual(img3.lonLat, None)
        self.assertEqual(img3.timestamp, None)
        img3.task()
        self.assertEqual(img.similar, None)
        self.assertEqual(img2.similar, None)
        self.assertEqual(img3.similar, img2)
        self.assertEqual(img2.similars.count(), 1)
        self.assertEqual(img2.similars.first(), img3)
        self.assertEqual(img3.lonLat, img2.lonLat)
        self.assertEqual(img3.timestamp, img2.timestamp)

    def test_exif_gps(self):
        exif = exif_lib.get_exif_data(PIL_Image.open('image/samples/gps_test.jpg'))
        lonLat = exif_lib.get_lon_lat(exif)
        point = GEOSGeometry('POINT(%f %f)' % lonLat)
        self.assertEqual(point.x, 127.103744)  # lon(경도)
        self.assertEqual(point.y, 37.399731)  # lat(위도)

        rf = RawFile()
        rf.file = self.uploadFile('gps_test.jpg')
        rf.save()

        img = Image()
        img.content = rf.url
        img.save()
        saved = Image.objects.first()

        self.assertEqual(img.lonLat, point)
        self.assertEqual(saved.lonLat, point)

    def test_exif_timestamp(self):
        exif = exif_lib.get_exif_data(PIL_Image.open('image/samples/gps_test.jpg'))
        timestamp = exif_lib.get_timestamp(exif)
        self.assertEqual(timestamp, 1459149534000)

        rf = RawFile()
        rf.file = self.uploadFile('gps_test.jpg')
        rf.save()

        img = Image()
        img.content = rf.url
        img.save()
        saved = Image.objects.first()

        self.assertEqual(img.timestamp, timestamp)
        self.assertEqual(saved.timestamp, timestamp)

    def test_no_exif(self):
        exif = exif_lib.get_exif_data(PIL_Image.open('image/samples/no_exif_test.jpg'))
        lonLat = exif_lib.get_lon_lat(exif)
        timestamp = exif_lib.get_timestamp(exif)
        self.assertIsNone(lonLat[0])
        self.assertIsNone(lonLat[1])
        self.assertIsNone(timestamp)

        rf = RawFile()
        rf.file = self.uploadFile('no_exif_test.jpg')
        rf.save()

        img = Image()
        img.content = rf.url
        img.save()
        saved = Image.objects.first()

        self.assertEqual(img.lonLat, None)
        self.assertEqual(img.timestamp, None)
        self.assertEqual(saved, img)
        self.assertEqual(saved.lonLat, None)
        self.assertEqual(saved.timestamp, None)

    def test_phash(self):
        rf = RawFile()
        rf.file = self.uploadFile('test.jpg')
        rf.save()
        rf2 = RawFile()
        rf2.file = self.uploadFile('test_480.jpg')
        rf2.save()

        img = Image()
        img.content = rf.url
        img.save()
        img.task()
        img2 = Image()
        img2.content = rf2.url
        img2.save()
        img2.task()

        self.assertNotEqual(img.phash, None)
        self.assertNotEqual(img2.phash, None)
        self.assertEqual(img.phash, img2.phash)

    def test_access_methods(self):
        img = Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()

        img.access()
        self.assertValidLocalFile(img.path_accessed)
        self.assertValidInternetUrl(img.url_accessed)

    def test_summarize_methods(self):
        img = Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()

        img.summarize()
        self.assertValidLocalFile(img.path_summarized)
        self.assertValidInternetUrl(img.url_summarized)

    def test_summarize_methods_2(self):
        img = Image()
        test_data = 'http://bookmarkimgs.naver.com/img/naver_profile.png'
        img.content = test_data
        img.save()

        img.summarize()
        self.assertValidLocalFile(img.path_summarized)
        self.assertValidInternetUrl(img.url_summarized)

    def test_json(self):
        img = Image()
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

        saved = Image.get_from_json(img.json)
        self.assertEqual(saved, img)
        self.assertEqual(saved.note, img.note)


class RawFileTest(APITestBase):

    def test_string_representation(self):
        rf_id = uuid1()
        rf = RawFile(id=rf_id)
        self.assertEqual(unicode(rf), '%s.rf' % b16encode(rf_id.bytes))
        self.assertEqual(rf.uuid, unicode(rf))

    def test_save_and_retreive(self):
        rf = RawFile()
        rf.file = self.uploadFile('test.png')
        rf.save()
        saved = RawFile.objects.first()
        self.assertEqual(saved, rf)
        self.assertEqual(saved.file, rf.file)

    def test_file_property(self):
        rf = RawFile()
        rf.file = self.uploadFile('test.png')
        rf.save()
        saved = RawFile.objects.first()

        url = rf.url
        regex = re_compile(r'^.*rfs/\d{4}/\d{1,2}/\d{1,2}/.+$')
        self.assertNotEqual(regex.match(url), None)
        self.assertEqual(saved, rf)
        self.assertEqual(saved.uuid, rf.uuid)
        self.assertEqual(saved.file, rf.file)

    def test_vd_property(self):
        vd = VD(); vd.save()
        rf = RawFile()
        rf.file = self.uploadFile('test.png')
        rf.vd = vd
        rf.save()
        saved = RawFile.objects.first()
        self.assertNotEqual(rf.vd, None)
        self.assertEqual(saved, rf)
        self.assertEqual(saved.vd, rf.vd)

    def test_image_cache(self):
        self.assertEqual(RawFile.objects.count(), 0)
        self.assertEqual(Image.objects.count(), 0)
        rf = RawFile()
        rf.file = self.uploadFile('test.JPEG')
        self.assertEqual(rf.ext, 'jpg')
        rf.save()
        self.assertEqual(rf.ext, 'jpg')
        self.assertEqual(RawFile.objects.count(), 1)
        self.assertEqual(Image.objects.count(), 1)

        img, is_created = Image.objects.get_or_create(content=rf.url)
        img.content = img.normalize_content(img.content)
        img.id = img._id
        self.assertValidLocalFile(img.path_accessed)
        self.assertValidInternetUrl(img.url_accessed)

        f = Path(img.path_accessed)
        self.assertEqual(f.is_symlink(), True)

        self.assertEqual(Image.objects.count(), 1)
        img.save()
        self.assertEqual(Image.objects.count(), 1)
        self.assertValidInternetUrl(img.url_accessed)
        self.assertValidInternetUrl(img.url_summarized)
        self.assertEqual(img, Image.objects.first())

        self.assertEqual(rf.img, img)
        self.assertEqual(img.rf, rf)
        img = Image.objects.first()
        rf = RawFile.objects.first()
        self.assertEqual(rf.img, img)
        self.assertEqual(img.rf, rf)

    def test_url_ext_property(self):
        rf = RawFile()
        rf.file = self.uploadFile('test.png')
        rf.save()
        saved = RawFile.objects.first()

        file_url = rf.file.url
        self.assertEqual(rf.url, '%s%s' % (SERVER_HOST, file_url))
        self.assertEqual(rf.url, saved.url)
        self.assertEqual(rf.ext, 'png')
        self.assertEqual(rf.ext, saved.ext)

    def test_task(self):
        rf = RawFile()
        rf.file = self.uploadFile('test.png')
        rf.save()
        saved = RawFile.objects.first()

        self.assertEqual(rf.mhash, None)
        rf.task()
        self.assertNotEqual(rf.mhash, None)
        self.assertEqual(rf.same, None)

        self.assertEqual(saved.mhash, None)
        saved.task()
        self.assertEqual(saved.mhash, rf.mhash)
        self.assertEqual(saved.same, rf.same)

        rf2 = RawFile()
        rf2.file = self.uploadFile('test.jpg')
        rf2.save()
        rf2.task()
        self.assertEqual(rf.same, None)
        self.assertEqual(rf2.same, None)

        rf3 = RawFile()
        rf3.file = self.uploadFile('test.png')
        rf3.save()
        rf3_old_file_path = rf3.file.path
        rf3.task()
        self.assertEqual(rf3.file.path, rf3_old_file_path)
        self.assertEqual(rf.same, None)
        self.assertEqual(rf2.same, None)
        self.assertEqual(rf3.same, rf)
        self.assertEqual(rf.sames.count(), 1)
        self.assertEqual(rf.sames.first(), rf3)

        f = Path(rf.file.path)
        f2 = Path(rf2.file.path)
        f3 = Path(rf3.file.path)
        self.assertEqual(f.is_symlink(), False)
        self.assertEqual(f2.is_symlink(), False)
        self.assertEqual(f3.is_symlink(), True)
