#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import UUID
from base64 import b16encode
from django.db import IntegrityError

from base.tests import APITestBase
from content.models import LegacyPlace, ShortText, PhoneNumber, LP_TYPE
from pathlib2 import Path
from place.models import Place


class LegacyPlaceTest(APITestBase):

    def test_string_representation_4square(self):
        lp = LegacyPlace()
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp.content = test_data
        self.assertEqual(unicode(lp), test_data)

    def test_save_and_retreive_4square(self):
        lp = LegacyPlace()
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], '4square')
        saved = LegacyPlace.objects.first()
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        saved2 = LegacyPlace.get_from_json('{"uuid": "%s", "content": null}' % lp.uuid)
        self.assertEqual(saved2.content, lp.content)
        saved3 = LegacyPlace.get_from_json('{"uuid": null, "content": "%s"}' % lp.content)
        self.assertEqual(saved3, lp)

    def test_content_property_4square_case1(self):
        lp = LegacyPlace()
        test_data = 'https://foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6'
        normalized_test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], '4square')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000001-4ccf-fc63-f637-8cfaace1b1d6'))

    def test_content_property_4square_case2(self):
        lp = LegacyPlace()
        test_data = 'http://foursquare.com/v/4ccffc63f6378cfaace1b1d6'
        normalized_test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], '4square')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000001-4ccf-fc63-f637-8cfaace1b1d6'))

    def test_content_property_naver_case1(self):
        lp = LegacyPlace()
        test_data = '21149144.naver'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'naver')
        saved = LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000002-0000-0000-0000-000021149144'))

    def test_content_property_naver_case2(self):
        lp = LegacyPlace()
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        normalized_test_data = '21149144.naver'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'naver')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000002-0000-0000-0000-000021149144'))

    def test_content_property_google_case1(self):
        lp = LegacyPlace()
        test_data = 'ChIJN1t_tDeuEmsRUsoyG83frY4.google'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'google')
        saved = LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('DB8EC763BF050034C79174B5DA189FC8'))

    def test_content_property_google_case2(self):
        lp = LegacyPlace()
        test_data = 'ChIJrTLr-GyuEmsRBfy61i59si0.google'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'google')
        saved = LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('fdc64a309ca7409a8a143be959307efe'))

    def __skip__test_access_methods1(self):
        lp = LegacyPlace()
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp.content = test_data
        lp.save()

        path = Path(lp.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        lp.access_force()
        self.assertEqual(path.exists(), True)

    def test_access_methods2(self):
        lp = LegacyPlace()
        test_data = '21149144.naver'
        lp.content = test_data
        lp.save()

        path = Path(lp.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        lp.access_force()
        self.assertEqual(path.exists(), True)

    def test_place_property(self):
        place = Place()
        place.save()

        self.assertEqual(LegacyPlace.objects.count(), 0)
        lp = LegacyPlace()
        self.assertEqual(lp.lp_type, None)
        lp.content = '21149144.naver'
        lp.save()
        self.assertEqual(LegacyPlace.objects.count(), 1)
        self.assertEqual(lp.place, None)
        self.assertEqual(lp.lp_type, LP_TYPE['naver'])

        lp2 = LegacyPlace()
        lp2.content = '21149144.naver'
        lp2.save()
        self.assertEqual(LegacyPlace.objects.count(), 1)
        self.assertEqual(lp2.place, None)
        self.assertEqual(lp2.lp_type, LP_TYPE['naver'])
        self.assertEqual(lp2, lp)

        lp3 = LegacyPlace()
        lp3.content = '21149145.naver'
        lp3.save()
        self.assertEqual(LegacyPlace.objects.count(), 2)
        self.assertEqual(lp3.place, None)
        self.assertEqual(lp3.lp_type, LP_TYPE['naver'])
        self.assertNotEqual(lp3, lp)

        lp.place = place
        lp.save()
        self.assertEqual(place.lps.first(), lp)

        lp3.place = place
        with self.assertRaises(IntegrityError):
            lp3.save()


class ShortTextTest(APITestBase):

    def test_string_representation(self):
        stxt = ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stxt.content = test_data
        self.assertEqual(unicode(stxt), test_data)

    def test_save_and_retreive(self):
        stxt = ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stxt.content = test_data
        stxt.save()
        saved = ShortText.objects.first()
        self.assertEqual(stxt.uuid, '%s.stxt' % b16encode(stxt.id.bytes))
        self.assertEqual(saved, stxt)
        self.assertEqual(saved.id, stxt.id)
        saved2 = ShortText.get_from_json('{"uuid": "%s", "content": null}' % stxt.uuid)
        self.assertEqual(saved2, stxt)
        saved3 = ShortText.get_from_json('{"uuid": null, "content": "%s"}' % stxt.content)
        self.assertEqual(saved3, stxt)

    def test_content_property(self):
        stxt = ShortText()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        stxt.content = test_data
        stxt.save()
        saved = ShortText.objects.first()
        self.assertEqual(stxt.content, test_data)
        self.assertEqual(saved, stxt)
        self.assertEqual(saved.id, stxt.id)
        self.assertEqual(saved.content, stxt.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        stxt = ShortText()
        test_data = '가끔 가면 맛있는 곳'
        stxt.content = test_data
        stxt.save()

        path = Path(stxt.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        stxt.access_force()
        self.assertEqual(path.exists(), True)


class PhoneNumberTest(APITestBase):

    def test_string_representation(self):
        phone = PhoneNumber()
        test_data = '+821055979245'
        phone.content = test_data
        self.assertEqual(unicode(phone), test_data)

    def test_save_and_retreive(self):
        phone = PhoneNumber()
        test_data = '+82 10-5597-9245'
        phone.content = test_data
        phone.save()
        saved = PhoneNumber.objects.first()
        self.assertEqual(phone.uuid, '%s.phone' % b16encode(phone.id.bytes))
        self.assertEqual(saved, phone)
        self.assertEqual(saved.id, phone.id)
        saved2 = PhoneNumber.get_from_json('{"uuid": "%s", "content": null}' % phone.uuid)
        self.assertEqual(saved2, phone)
        saved3 = PhoneNumber.get_from_json('{"uuid": null, "content": "%s"}' % phone.content)
        self.assertEqual(saved3, phone)

    def test_content_property(self):
        phone = PhoneNumber()
        test_data = '010-5597-9245'
        phone.content = test_data
        phone.save()
        saved = PhoneNumber.objects.first()
        normalized_data = PhoneNumber.normalize_content(test_data)
        self.assertEqual(phone.content, normalized_data)
        self.assertEqual(saved, phone)
        self.assertEqual(saved.id, phone.id)
        self.assertEqual(saved.content, phone.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        phone = PhoneNumber()
        test_data = '031-724-2733'
        phone.content = test_data
        phone.save()

        path = Path(phone.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        phone.access_force()
        self.assertEqual(path.exists(), True)
