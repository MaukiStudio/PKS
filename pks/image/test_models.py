#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1, UUID
from base64 import b16encode
from django.contrib.gis.geos import GEOSGeometry
from re import compile as re_compile

from base.tests import APITestBase
from image.models import Image, RawFile, AzurePrediction, CONVERTED_DNS_LIST
from PIL import Image as PIL_Image
from base.legacy import exif_lib
from account.models import VD
from base.utils import get_timestamp
from content.models import ImageNote
from pks.settings import SERVER_HOST, WORK_ENVIRONMENT
from pathlib2 import Path
from tag.models import ImageTags, Tag


class ImageTest(APITestBase):

    def test_string_representation(self):
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img, is_created = Image.get_or_create_smart(test_data)
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
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img, is_created = Image.get_or_create_smart(test_data)
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

        rf4 = RawFile()
        rf4.file = self.uploadFile('test.jpg')
        rf4.save()
        img4, is_created = Image.get_or_create_smart(rf4.url)
        self.assertNotEqual(img4.content, rf4.url)
        self.assertEqual(img4.url_for_access, rf4.url)
        self.assertEqual(img4.url_for_access.endswith(img4.content), True)

    def test_phash_hamming_dist(self):
        id_640 = Image.compute_phash(PIL_Image.open('image/samples/test.jpg'))
        id_256 = Image.compute_phash(PIL_Image.open('image/samples/test_256.jpg'))
        id_480 = Image.compute_phash(PIL_Image.open('image/samples/test_480.jpg'))
        #id_1200 = Image.compute_phash(PIL_Image.open('image/samples/test_1200.jpg'))
        #id_org = Image.compute_phash(PIL_Image.open('image/samples/test_org.jpg'))
        id2 = Image.compute_phash(PIL_Image.open('image/samples/no_exif_test.jpg'))

        self.assertLessEqual(Image.hamming_distance(id_640, id_256), 2)
        self.assertLessEqual(Image.hamming_distance(id_640, id_480), 2)
        #self.assertLessEqual(Image.hamming_distance(id_640, id_1200), 2)
        #self.assertLessEqual(Image.hamming_distance(id_640, id_org), 0)
        self.assertGreater(Image.hamming_distance(id_640, id2), 36)  # distance = 69

    def test_dhash_hamming_dist(self):
        id_640 = Image.compute_dhash(PIL_Image.open('image/samples/test.jpg'))
        id_256 = Image.compute_dhash(PIL_Image.open('image/samples/test_256.jpg'))
        id_480 = Image.compute_dhash(PIL_Image.open('image/samples/test_480.jpg'))
        #id_1200 = Image.compute_dhash(PIL_Image.open('image/samples/test_1200.jpg'))
        #id_org = Image.compute_dhash(PIL_Image.open('image/samples/test_org.jpg'))
        id2 = Image.compute_dhash(PIL_Image.open('image/samples/no_exif_test.jpg'))

        self.assertLessEqual(Image.hamming_distance(id_640, id_256), 0)
        self.assertLessEqual(Image.hamming_distance(id_640, id_480), 0)
        #self.assertLessEqual(Image.hamming_distance(id_640, id_1200), 0)
        #self.assertLessEqual(Image.hamming_distance(id_640, id_org), 0)
        self.assertGreater(Image.hamming_distance(id_640, id2), 3)  # distance = 15

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
        self.assertEqual(saved.dhash, img.dhash)
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
        point = GEOSGeometry('POINT(%f %f)' % lonLat, srid=4326)
        self.assertEqual(point.x, 127.103744)  # lon(경도)
        self.assertEqual(point.y, 37.399731)  # lat(위도)

        rf = RawFile()
        rf.file = self.uploadFile('gps_test.jpg')
        rf.save()

        img, is_created = Image.get_or_create_smart(rf.url)
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

        img, is_created = Image.get_or_create_smart(rf.url)
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

        img, is_created = Image.get_or_create_smart(rf.url)
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
        rf2.file = self.uploadFile('test.jpg')
        rf2.save()

        img, is_created = Image.get_or_create_smart(rf.url)
        img2, is_created = Image.get_or_create_smart(rf2.url)

        self.assertNotEqual(img.phash, None)
        self.assertNotEqual(img2.phash, None)
        self.assertEqual(img.phash, img2.phash)

    def test_dhash(self):
        rf = RawFile()
        rf.file = self.uploadFile('test.jpg')
        rf.save()
        rf2 = RawFile()
        rf2.file = self.uploadFile('test_480.jpg')
        rf2.save()

        img, is_created = Image.get_or_create_smart(rf.url)
        img2, is_created = Image.get_or_create_smart(rf2.url)

        self.assertNotEqual(img.dhash, None)
        self.assertNotEqual(img2.dhash, None)
        self.assertEqual(img.dhash, img2.dhash)

    def test_save(self):
        rf = RawFile()
        rf.file = self.uploadFile('test_transpose.jpg')
        rf.save()
        img = rf.img
        timestamp = img.timestamp
        lonLat = img.lonLat
        self.assertNotEqual(timestamp, None)
        self.assertNotEqual(lonLat, None)

        img.timestamp = None
        img.lonLat = None
        self.assertEqual(img.timestamp, None)
        self.assertEqual(img.lonLat, None)
        img.save()
        self.assertNotEqual(img.timestamp, None)
        self.assertNotEqual(img.lonLat, None)
        img.timestamp = 0
        img.lonLat = None
        img.save()
        self.assertEqual(img.timestamp, timestamp)
        self.assertEqual(img.lonLat, lonLat)

    # id 값은 보존하면서 content 값을 바꾸려던 구현 시도
    # 로그성으로 남겨둠
    '''
    def test_save2(self):
        old_url = 'http://maukitest.cloudapp.net/media/rfs/2016/07/15/00000155ED9687CD0000000000D4F4A6.rf_image.jpg'
        img, is_created = Image.get_or_create_smart(old_url)
        self.assertEqual(is_created, True)
        self.assertEqual(Image.objects.count(), 1)
        saved_id = Image.objects.first().id
        self.assertEqual(img.id, saved_id)

        img.content = old_url
        img.save()
        self.assertEqual(Image.objects.count(), 1)
        self.assertEqual(img.id, saved_id)

        converted = CONVERTED_DNS_LIST[0]
        img.content = img.content.replace(converted[0], converted[1])
        img.save()
        self.assertEqual(Image.objects.count(), 1)
        self.assertEqual(img.id, saved_id)

        #img2, is_created = Image.get_or_create_smart(old_url)
        #self.assertEqual(is_created, False)
        #self.assertEqual(img2, img)
        img3, is_created = Image.get_or_create_smart(img.content)
        self.assertEqual(is_created, False)
        self.assertEqual(img3, img)

        img.content = old_url
        img.save()
        self.assertEqual(Image.objects.count(), 1)
        self.assertEqual(img.id, saved_id)

        img.content = img.content.replace(converted[0], 'bad.domain.com')
        with self.assertRaises(NotImplementedError):
            img.save()
    '''

    def test_transpose(self):
        rf = RawFile()
        rf.file = self.uploadFile('test_transpose.jpg')
        rf.save()
        img = rf.img
        timestamp = img.timestamp
        lonLat = img.lonLat

        self.assertNotEqual(lonLat, None)
        self.assertNotEqual(timestamp, None)

    def test_access_methods(self):
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img, is_created = Image.get_or_create_smart(test_data)
        img.access()
        self.assertValidLocalFile(img.path_accessed)
        self.assertValidInternetUrl(img.url_accessed)

    def test_access_methods2(self):
        test_data = 'http://maukitest.cloudapp.net/media/rfs/2016/07/15/00000155ED9687CD0000000000D4F4A6.rf_image.jpg?1463275413000'
        img, is_created = Image.get_or_create_smart(test_data)
        img.access()
        self.assertValidLocalFile(img.path_accessed)
        self.assertValidInternetUrl(img.url_accessed)

    def test_summarize_methods(self):
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img, is_created = Image.get_or_create_smart(test_data)
        img.summarize()
        self.assertValidLocalFile(img.path_summarized)
        self.assertValidInternetUrl(img.url_summarized)

    def test_summarize_methods_2(self):
        test_data = 'http://bookmarkimgs.naver.com/img/naver_profile.png'
        img, is_created = Image.get_or_create_smart(test_data)
        img.summarize()
        self.assertValidLocalFile(img.path_summarized)
        self.assertValidInternetUrl(img.url_summarized)

    def test_json(self):
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img, is_created = Image.get_or_create_smart(test_data)
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
        #self.assertIn('timestamp', img.json)
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

        img, is_created = Image.get_or_create_smart(rf.url)
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

        rf.task()
        rf2.task()
        f = Path(rf.file.path)
        f2 = Path(rf2.file.path)
        f3 = Path(rf3.file.path)
        self.assertEqual(f.is_symlink(), False)
        self.assertEqual(f2.is_symlink(), False)
        self.assertEqual(f3.is_symlink(), True)

        rf4 = RawFile()
        rf4.file = self.uploadFile('test_org.jpg')
        rf4.save()
        self.assertEqual(rf4.mhash, None)
        pil4_1 = PIL_Image.open(rf4.file.path)
        self.assertEqual(pil4_1.size, (4160, 2340))
        rf4.task()
        self.assertEqual(rf4.mhash, UUID('11d2db89-67e0-d22a-d294-94ce76ef0e56'))
        pil4_2 = PIL_Image.open(rf4.file.path)
        self.assertEqual(pil4_2.size, (1280, 720))

        rf4.task()
        self.assertEqual(rf4.mhash, UUID('11d2db89-67e0-d22a-d294-94ce76ef0e56'))
        pil4_3 = PIL_Image.open(rf4.file.path)
        self.assertEqual(pil4_3.size, (1280, 720))


class AzurePredictionTest(APITestBase):

    def test_analyze(self):
        if WORK_ENVIRONMENT: return
        img_url = 'http://pds.joins.com/news/component/starnews/201607/14/2016071408355459431_1.jpg'
        img, is_created = Image.get_or_create_smart(img_url)
        azure = AzurePrediction.objects.create(img=img)
        r = azure.predict()
        #print(r)
        self.assertNotEqual(r, None)
        self.assertEqual(img.azure, azure)
        self.assertEqual(azure.is_success_analyze, True)
        self.assertNotEqual(azure.result_analyze, None)

        imgTags = ImageTags.objects.first()
        #imgTags.dump()
        self.assertEqual(imgTags.img, img)
        self.assertEqual(img.ctags, imgTags)
        self.assertNotEqual(imgTags, None)
        self.assertNotEqual(imgTags.tags, None)
        self.assertEqual(len(imgTags.tags), 11)
