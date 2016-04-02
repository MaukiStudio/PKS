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
        fs.content = test_data
        self.assertEqual(unicode(fs), test_data)

    def test_save_and_retreive(self):
        fs = models.FsVenue()
        fs.id = uuid1()
        fs.save()
        saved = models.FsVenue.objects.first()
        self.assertEqual(saved, fs)
        self.assertEqual(saved.id, fs.id)
        saved2 = models.FsVenue.get_from_uuid(fs.uuid)
        self.assertEqual(saved2, fs)

    def test_content_property(self):
        fs = models.FsVenue()
        test_data = '40a55d80f964a52020f31ee3'
        fs.content = test_data
        fs.save()
        saved = models.FsVenue.objects.first()
        self.assertEqual(fs.content, test_data)
        self.assertEqual(saved, fs)
        self.assertEqual(saved.id, fs.id)
        self.assertEqual(saved.content, fs.content)
        self.assertEqual(saved.id, UUID('00000000-40a5-5d80-f964-a52020f31ee3'))


class ShortTextTest(APITestBase):

    def test_string_representation(self):
        stxt = models.ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stxt.content = test_data
        self.assertEqual(unicode(stxt), test_data)

    def test_save_and_retreive(self):
        stxt = models.ShortText()
        test_id = uuid1()
        stxt.id = test_id
        stxt.save()
        saved = models.ShortText.objects.first()
        self.assertEqual(stxt.id, test_id)
        self.assertEqual(stxt.uuid, '%s.stxt' % b16encode(test_id.bytes))
        self.assertEqual(saved, stxt)
        self.assertEqual(saved.id, test_id)
        saved2 = models.ShortText.get_from_uuid(stxt.uuid)
        self.assertEqual(saved2, stxt)

    def test_content_property(self):
        stxt = models.ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stxt.content = test_data
        stxt.save()
        saved = models.ShortText.objects.first()
        self.assertEqual(stxt.content, test_data)
        self.assertEqual(saved, stxt)
        self.assertEqual(saved.id, stxt.id)
        self.assertEqual(saved.content, stxt.content)
