#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import UUID

from base.tests import APITestBase
from image.models import Image, RawFile
from pks.settings import DISABLE_NO_FREE_API


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
        rf = RawFile.objects.get(id=rf.id)
        self.assertEqual(rf.mhash, UUID('5abd147d-ceb8-218a-a160-1c7821db6654'))
