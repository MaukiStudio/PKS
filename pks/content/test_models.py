#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import UUID
from base64 import b16encode

from base.tests import APITestBase
from content import models


class LegacyPlaceTest(APITestBase):

    def test_string_representation_4square(self):
        lp = models.LegacyPlace()
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp.content = test_data
        self.assertEqual(unicode(lp), test_data)

    def test_save_and_retreive_4square(self):
        lp = models.LegacyPlace()
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], '4square')
        saved = models.LegacyPlace.objects.first()
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        saved2 = models.LegacyPlace.get_from_json('{"uuid": "%s", "content": null}' % lp.uuid)
        self.assertEqual(saved2.content, lp.content)
        saved3 = models.LegacyPlace.get_from_json('{"uuid": null, "content": "%s"}' % lp.content)
        self.assertEqual(saved3, lp)

    def test_content_property_4square_case1(self):
        lp = models.LegacyPlace()
        test_data = 'https://foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6'
        normalized_test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], '4square')
        saved = models.LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000001-4ccf-fc63-f637-8cfaace1b1d6'))

    def test_content_property_4square_case2(self):
        lp = models.LegacyPlace()
        test_data = 'http://foursquare.com/v/4ccffc63f6378cfaace1b1d6'
        normalized_test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], '4square')
        saved = models.LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000001-4ccf-fc63-f637-8cfaace1b1d6'))

    def test_content_property_naver_case1(self):
        lp = models.LegacyPlace()
        test_data = '21149144.naver'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'naver')
        saved = models.LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000002-0000-0000-0000-000021149144'))

    def test_content_property_naver_case2(self):
        lp = models.LegacyPlace()
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        normalized_test_data = '21149144.naver'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'naver')
        saved = models.LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000002-0000-0000-0000-000021149144'))

    def test_content_property_google_case1(self):
        lp = models.LegacyPlace()
        test_data = 'ChIJN1t_tDeuEmsRUsoyG83frY4.google'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'google')
        saved = models.LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('DB8EC763BF050034C79174B5DA189FC8'))

    def test_content_property_google_case2(self):
        lp = models.LegacyPlace()
        test_data = 'ChIJrTLr-GyuEmsRBfy61i59si0.google'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'google')
        saved = models.LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('fdc64a309ca7409a8a143be959307efe'))


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


class PhoneNumberTest(APITestBase):

    def test_string_representation(self):
        phone = models.PhoneNumber()
        test_data = '+821055979245'
        phone.content = test_data
        self.assertEqual(unicode(phone), test_data)

    def test_save_and_retreive(self):
        phone = models.PhoneNumber()
        test_data = '+82 10-5597-9245'
        phone.content = test_data
        phone.save()
        saved = models.PhoneNumber.objects.first()
        self.assertEqual(phone.uuid, '%s.phone' % b16encode(phone.id.bytes))
        self.assertEqual(saved, phone)
        self.assertEqual(saved.id, phone.id)
        saved2 = models.PhoneNumber.get_from_json('{"uuid": "%s", "content": null}' % phone.uuid)
        self.assertEqual(saved2, phone)
        saved3 = models.PhoneNumber.get_from_json('{"uuid": null, "content": "%s"}' % phone.content)
        self.assertEqual(saved3, phone)

    def test_content_property(self):
        phone = models.PhoneNumber()
        test_data = '010-5597-9245'
        phone.content = test_data
        phone.save()
        saved = models.PhoneNumber.objects.first()
        normalized_data = models.PhoneNumber.normalize_content(test_data)
        self.assertEqual(phone.content, normalized_data)
        self.assertEqual(saved, phone)
        self.assertEqual(saved.id, phone.id)
        self.assertEqual(saved.content, phone.content)
