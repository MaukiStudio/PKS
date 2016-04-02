#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1, UUID
from base64 import b16encode

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
        stxt = models.ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stxt.content = test_data
        self.assertEqual(unicode(stxt), test_data)

    def test_save_and_retreive(self):
        stxt = models.ShortText()
        test_uuid = uuid1()
        stxt.uuid = test_uuid
        stxt.save()
        saved = models.ShortText.objects.first()
        self.assertEqual(stxt.uuid, test_uuid)
        self.assertEqual(stxt.uuid_json, '%s.stxt' % b16encode(test_uuid.bytes))
        self.assertEqual(saved, stxt)
        self.assertEqual(saved.uuid, test_uuid)

    def test_content_property(self):
        stxt = models.ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stxt.content = test_data
        stxt.save()
        saved = models.ShortText.objects.first()
        self.assertEqual(stxt.content, test_data)
        self.assertEqual(saved, stxt)
        self.assertEqual(saved.uuid, stxt.uuid)
        self.assertEqual(saved.content, stxt.content)
