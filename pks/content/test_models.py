#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import UUID
from base64 import b16encode
from django.db import IntegrityError

from base.tests import APITestBase
from content.models import LegacyPlace, PhoneNumber, LP_TYPE, PlaceName, Address, PlaceNote, ImageNote
from pathlib2 import Path
from place.models import Place
from url.models import Url


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
        self.assertEqual(lp.lp_type, 1)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000001-4ccf-fc63-f637-8cfaace1b1d6'))
        self.assertEqual(saved.lp_type, 1)

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
        self.assertEqual(lp.lp_type, 2)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000002-0000-0000-0000-000021149144'))
        self.assertEqual(saved.lp_type, 2)

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
        self.assertEqual(lp.lp_type, 3)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('DB8EC763BF050034C79174B5DA189FC8'))
        self.assertEqual(saved.lp_type, 3)

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

    def test_content_property_kakao_case1(self):
        lp = LegacyPlace()
        test_data = '14720610.kakao'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'kakao')
        saved = LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(lp.lp_type, 4)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000004-0000-0000-0000-000014720610'))
        self.assertEqual(saved.lp_type, 4)

    def test_content_property_kakao_case2(self):
        lp = LegacyPlace()
        test_data = 'https://place.kakao.com/places/14720610/홍콩'
        normalized_test_data = '14720610.kakao'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'kakao')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000004-0000-0000-0000-000014720610'))

    def test_content_property_kakao_case3(self):
        lp = LegacyPlace()
        test_data = 'http://place.kakao.com/places/14720610'
        normalized_test_data = '14720610.kakao'
        lp.content = test_data
        lp.save()
        self.assertEqual(lp.uuid.split('.')[1], 'kakao')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000004-0000-0000-0000-000014720610'))

    def __skip__test_access_by_4square(self):
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

    def test_access_by_naver(self):
        lp = LegacyPlace()
        test_data = '21149144.naver'
        lp.content = test_data
        lp.save()
        path = Path(lp.path_accessed)
        if path.exists():
            path.unlink()
        self.assertEqual(path.exists(), False)
        lp.access()
        self.assertEqual(path.exists(), True)

    def test_access_by_kakao(self):
        lp = LegacyPlace()
        test_data = '14720610.kakao'
        lp.content = test_data
        lp.save()
        path = Path(lp.path_accessed)
        if path.exists():
            path.unlink()
        self.assertEqual(path.exists(), False)
        lp.access()
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

    def test_get_from_url(self):
        url = Url(content='http://map.naver.com/local/siteview.nhn?code=21149144')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '21149144.naver')

        url = Url(content='http://map.naver.com/?app=Y&version=10&appMenu=location&pinId=31130096&pinType=site&lat=37.3916387&lng=127.0584149&title=능이향기&dlevel=11')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '31130096.naver')

        url = Url(content='http://m.store.naver.com/restaurants/detail?id=37333252')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '37333252.naver')

        url = Url(content='http://m.map.naver.com/siteview.nhn?code=31176899')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '31176899.naver')


        url = Url(content='http://place.kakao.com/places/14720610')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '14720610.kakao')

        url = Url(content='https://foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '4ccffc63f6378cfaace1b1d6.4square')

        url = Url(content='http://foursquare.com/v/4ccffc63f6378cfaace1b1d6')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '4ccffc63f6378cfaace1b1d6.4square')

    def test_access_methods(self):
        lp = LegacyPlace()
        test_data = '31130096.naver'
        lp.content = test_data
        lp.save()

        lp.access()
        self.assertValidLocalFile(lp.path_accessed)
        self.assertValidInternetUrl(lp.url_accessed)

    def test_summarize_methods(self):
        lp = LegacyPlace()
        test_data = '37333252.naver'
        lp.content = test_data
        lp.save()

        lp.summarize()
        self.assertValidLocalFile(lp.path_summarized)
        self.assertValidInternetUrl(lp.url_summarized)

    def test_content_summarized_by_naver(self):
        lp = LegacyPlace()
        test_data = '21149144.naver'
        lp.content = test_data
        lp.save()
        lp.summarize()
        pb = lp.content_summarized
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, '방아깐')

    def test_content_summarized_by_kakao(self):
        lp = LegacyPlace()
        test_data = '14720610.kakao'
        lp.content = test_data
        lp.save()
        lp.summarize()
        pb = lp.content_summarized
        self.printJson(pb)
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, '홍콩')


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


class PlaceNameTest(APITestBase):

    def test_string_representation(self):
        pname = PlaceName()
        test_data = '방아깐'
        pname.content = test_data
        self.assertEqual(unicode(pname), test_data)

    def test_save_and_retreive(self):
        pname = PlaceName()
        test_data = '방아깐'
        pname.content = test_data
        pname.save()
        saved = PlaceName.objects.first()
        self.assertEqual(pname.uuid, '%s.pname' % b16encode(pname.id.bytes))
        self.assertEqual(saved, pname)
        self.assertEqual(saved.id, pname.id)
        saved2 = PlaceName.get_from_json('{"uuid": "%s", "content": null}' % pname.uuid)
        self.assertEqual(saved2, pname)
        saved3 = PlaceName.get_from_json('{"uuid": null, "content": "%s"}' % pname.content)
        self.assertEqual(saved3, pname)

    def test_content_property(self):
        pname = PlaceName()
        test_data = '방아깐'
        pname.content = test_data
        pname.save()
        saved = PlaceName.objects.first()
        self.assertEqual(pname.content, test_data)
        self.assertEqual(saved, pname)
        self.assertEqual(saved.id, pname.id)
        self.assertEqual(saved.content, pname.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        pname = PlaceName()
        test_data = '방아깐'
        pname.content = test_data
        pname.save()

        path = Path(pname.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        pname.access_force()
        self.assertEqual(path.exists(), True)


class AddressTest(APITestBase):

    def test_string_representation(self):
        addr = Address()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr.content = test_data
        self.assertEqual(unicode(addr), test_data)

    def test_save_and_retreive(self):
        addr = Address()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr.content = test_data
        addr.save()
        saved = Address.objects.first()
        self.assertEqual(addr.uuid, '%s.addr' % b16encode(addr.id.bytes))
        self.assertEqual(saved, addr)
        self.assertEqual(saved.id, addr.id)
        saved2 = Address.get_from_json('{"uuid": "%s", "content": null}' % addr.uuid)
        self.assertEqual(saved2, addr)
        saved3 = Address.get_from_json('{"uuid": null, "content": "%s"}' % addr.content)
        self.assertEqual(saved3, addr)

    def test_content_property(self):
        addr = Address()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr.content = test_data
        addr.save()
        saved = Address.objects.first()
        self.assertEqual(addr.content, test_data)
        self.assertEqual(saved, addr)
        self.assertEqual(saved.id, addr.id)
        self.assertEqual(saved.content, addr.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        addr = Address()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr.content = test_data
        addr.save()

        path = Path(addr.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        addr.access_force()
        self.assertEqual(path.exists(), True)


class PlaceNoteTest(APITestBase):

    def test_string_representation(self):
        pnote = PlaceNote()
        test_data = '능이백숙 국물 죽이네~ ㅎㅎ'
        pnote.content = test_data
        self.assertEqual(unicode(pnote), test_data)

    def test_save_and_retreive(self):
        pnote = PlaceNote()
        test_data = '능이백숙 국물 죽이네~ ㅎㅎ'
        pnote.content = test_data
        pnote.save()
        saved = PlaceNote.objects.first()
        self.assertEqual(pnote.uuid, '%s.pnote' % b16encode(pnote.id.bytes))
        self.assertEqual(saved, pnote)
        self.assertEqual(saved.id, pnote.id)
        saved2 = PlaceNote.get_from_json('{"uuid": "%s", "content": null}' % pnote.uuid)
        self.assertEqual(saved2, pnote)
        saved3 = PlaceNote.get_from_json('{"uuid": null, "content": "%s"}' % pnote.content)
        self.assertEqual(saved3, pnote)

    def test_content_property(self):
        pnote = PlaceNote()
        test_data = '능이백숙 국물 죽이네~ ㅎㅎ'
        pnote.content = test_data
        pnote.save()
        saved = PlaceNote.objects.first()
        self.assertEqual(pnote.content, test_data)
        self.assertEqual(saved, pnote)
        self.assertEqual(saved.id, pnote.id)
        self.assertEqual(saved.content, pnote.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        pnote = PlaceNote()
        test_data = '능이백숙 국물 죽이네~ ㅎㅎ'
        pnote.content = test_data
        pnote.save()

        path = Path(pnote.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        pnote.access_force()
        self.assertEqual(path.exists(), True)


class ImageNoteTest(APITestBase):

    def test_string_representation(self):
        inote = ImageNote()
        test_data = '자기랑 진우랑 찰칵~ ^^'
        inote.content = test_data
        self.assertEqual(unicode(inote), test_data)

    def test_save_and_retreive(self):
        inote = ImageNote()
        test_data = '자기랑 진우랑 찰칵~ ^^'
        inote.content = test_data
        inote.save()
        saved = ImageNote.objects.first()
        self.assertEqual(inote.uuid, '%s.inote' % b16encode(inote.id.bytes))
        self.assertEqual(saved, inote)
        self.assertEqual(saved.id, inote.id)
        saved2 = ImageNote.get_from_json('{"uuid": "%s", "content": null}' % inote.uuid)
        self.assertEqual(saved2, inote)
        saved3 = ImageNote.get_from_json('{"uuid": null, "content": "%s"}' % inote.content)
        self.assertEqual(saved3, inote)

    def test_content_property(self):
        inote = ImageNote()
        test_data = '자기랑 진우랑 찰칵~ ^^'
        inote.content = test_data
        inote.save()
        saved = ImageNote.objects.first()
        self.assertEqual(inote.content, test_data)
        self.assertEqual(saved, inote)
        self.assertEqual(saved.id, inote.id)
        self.assertEqual(saved.content, inote.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        inote = ImageNote()
        test_data = '자기랑 진우랑 찰칵~ ^^'
        inote.content = test_data
        inote.save()

        path = Path(inote.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        inote.access_force()
        self.assertEqual(path.exists(), True)

