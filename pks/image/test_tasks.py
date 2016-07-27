#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import UUID

from base.tests import APITestBase
from image.models import Image, RawFile, AzurePrediction
from pks.settings import DISABLE_NO_FREE_API
from tag.models import ImageTags


class TaskTest(APITestBase):

    def test_img_task(self):
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img, is_created = Image.get_or_create_smart(test_data)
        img = Image.objects.get(id=img.id)
        self.assertEqual(img.dhash, 12116166)
        self.assertEqual(img.phash, UUID('0017c0a8-a6ed-a0c5-1230-8ef6eb5176fe'))
        self.assertNotEqual(img.azure, None)

        if not DISABLE_NO_FREE_API:
            self.assertEqual(img.azure.is_success_analyze, True)
            self.assertEqual(len(img.ctags.tags), 8)

    def test_rf_task(self):
        rf = RawFile()
        rf.file = self.uploadFile('test.png')
        rf.save()
        rf.task()
        rf = RawFile.objects.get(id=rf.id)
        self.assertEqual(rf.mhash, UUID('5abd147d-ceb8-218a-a160-1c7821db6654'))


class AzurePredictionTest(APITestBase):

    def test_analyze(self):
        if DISABLE_NO_FREE_API: return
        img_url = 'http://pds.joins.com/news/component/starnews/201607/14/2016071408355459431_1.jpg'
        img, is_created = Image.get_or_create_smart(img_url)
        azure, is_created = AzurePrediction.objects.get_or_create(img=img)
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

        #self.fail()
