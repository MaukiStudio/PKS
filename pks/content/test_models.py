#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1, UUID
from base64 import b16encode

from base.tests import APITestBase
from content import models


class LegacyPlaceTest(APITestBase):

    def test_string_representation_4square(self):
        lp = models.LegacyPlace()
        test_data = '40a55d80f964a52020f31ee3.4square'
        lp.content = test_data
        self.assertEqual(unicode(lp), test_data)

    def test_save_and_retreive_4square(self):
        lp = models.LegacyPlace()
        test_data = '40a55d80f964a52020f31ee3.4square'
        lp.content = test_data
        lp.save()
        saved = models.LegacyPlace.objects.first()
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        saved2 = models.LegacyPlace.get_from_json('{"uuid": "%s", "content": null}' % lp.uuid)
        self.assertEqual(saved2, lp)
        saved3 = models.LegacyPlace.get_from_json('{"uuid": null, "content": "%s"}' % lp.content)
        self.assertEqual(saved3, lp)

    def test_content_property_4square(self):
        lp = models.LegacyPlace()
        test_data = '40a55d80f964a52020f31ee3.4square'
        lp.content = test_data
        lp.save()
        saved = models.LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000001-40a5-5d80-f964-a52020f31ee3'))


class ShortTextTest(APITestBase):

    def test_string_representation(self):
        stxt = models.ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stxt.content = test_data
        self.assertEqual(unicode(stxt), test_data)

    def test_save_and_retreive(self):
        stxt = models.ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stxt.content = test_data
        stxt.save()
        saved = models.ShortText.objects.first()
        self.assertEqual(stxt.uuid, '%s.stxt' % b16encode(stxt.id.bytes))
        self.assertEqual(saved, stxt)
        self.assertEqual(saved.id, stxt.id)
        saved2 = models.ShortText.get_from_json('{"uuid": "%s", "content": null}' % stxt.uuid)
        self.assertEqual(saved2, stxt)
        saved3 = models.ShortText.get_from_json('{"uuid": null, "content": "%s"}' % stxt.content)
        self.assertEqual(saved3, stxt)

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
