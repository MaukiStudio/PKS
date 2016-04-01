#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1, UUID

from base.tests import APITestBase
from content import models


class FsVenueTest(APITestBase):

    def test_string_representation(self):
        fs = models.FsVenue()
        test_data = '40a55d80f964a52020f31ee3'
        fs.fsVenueId = test_data
        self.assertEqual(unicode(fs), test_data)

    def test_save_and_retreive(self):
        fs = models.FsVenue()
        fs.uuid = uuid1()
        fs.save()
        saved = models.FsVenue.objects.first()
        self.assertEqual(saved, fs)
        self.assertEqual(saved.uuid, fs.uuid)

    def test_fsVenueId_property(self):
        fs = models.FsVenue()
        test_data = '40a55d80f964a52020f31ee3'
        fs.fsVenueId = test_data
        fs.save()
        saved = models.FsVenue.objects.first()
        self.assertEqual(fs.fsVenueId, test_data)
        self.assertEqual(saved, fs)
        self.assertEqual(saved.uuid, fs.uuid)
        self.assertEqual(saved.fsVenueId, fs.fsVenueId)
        self.assertEqual(saved.uuid, UUID('00000000-40a5-5d80-f964-a52020f31ee3'))


class ShortTextTest(APITestBase):

    def test_string_representation(self):
        stext = models.ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stext.content = test_data
        self.assertEqual(unicode(stext), test_data)

    def test_save_and_retreive(self):
        stext = models.ShortText()
        stext.uuid = uuid1()
        stext.save()
        saved = models.ShortText.objects.first()
        self.assertEqual(saved, stext)
        self.assertEqual(saved.uuid, stext.uuid)

    def test_content_property(self):
        stext = models.ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stext.content = test_data
        stext.save()
        saved = models.ShortText.objects.first()
        self.assertEqual(stext.content, test_data)
        self.assertEqual(saved, stext)
        self.assertEqual(saved.uuid, stext.uuid)
        self.assertEqual(saved.content, stext.content)
