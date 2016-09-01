#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import UUID
from base64 import b16encode
from django.db import IntegrityError
from urllib import unquote_plus

from base.tests import APITestBase
from content.models import LegacyPlace, PhoneNumber, LP_TYPE, PlaceName, Address, PlaceNote, ImageNote, TagName
from pathlib2 import Path
from place.models import Place
from url.models import Url
from pks.settings import WORK_ENVIRONMENT


class LegacyPlaceTest(APITestBase):

    def test_string_representation_4square(self):
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(unicode(lp), test_data)

    def test_save_and_retreive_4square(self):
        if WORK_ENVIRONMENT: return
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], '4square')
        saved = LegacyPlace.objects.first()
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        saved2 = LegacyPlace.get_from_json('{"uuid": "%s", "content": null}' % lp.uuid)
        self.assertEqual(saved2.content, lp.content)
        saved3 = LegacyPlace.get_from_json('{"uuid": null, "content": "%s"}' % lp.content)
        self.assertEqual(saved3, lp)

    def test_content_property_4square_case1(self):
        if WORK_ENVIRONMENT: return
        test_data = 'https://foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6'
        normalized_test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
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
        if WORK_ENVIRONMENT: return
        test_data = 'http://foursquare.com/v/4ccffc63f6378cfaace1b1d6'
        normalized_test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], '4square')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000001-4ccf-fc63-f637-8cfaace1b1d6'))

    def _skip_test_content_property_naver_case1(self):
        test_data = '21149144.naver'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], 'naver')
        saved = LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(lp.lp_type, 2)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000002-0000-0000-0000-000021149144'))
        self.assertEqual(saved.lp_type, 2)

    def _skip_test_content_property_naver_case2(self):
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        normalized_test_data = '21149144.naver'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], 'naver')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000002-0000-0000-0000-000021149144'))

    def _skip_test_content_property_naver_case3(self):
        test_data = 'http://map.naver.com/?app=Y&version=10&appMenu=location&pinId=36229742&pinType=site&lat=37.4893023&lng=127.1350392&title=%EB%B0%94%EC%9D%B4%ED%82%A4%20%EB%AC%B8%EC%A0%95%EC%A0%90&dlevel=11'
        normalized_test_data = '36229742.naver'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], 'naver')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000002-0000-0000-0000-000036229742'))

    def test_content_property_google_case1(self):
        if WORK_ENVIRONMENT: return
        test_data = 'ChIJN1t_tDeuEmsRUsoyG83frY4.google'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
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
        if WORK_ENVIRONMENT: return
        test_data = 'ChIJrTLr-GyuEmsRBfy61i59si0.google'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], 'google')
        saved = LegacyPlace.objects.first()
        self.assertEqual(lp.content, test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('fdc64a309ca7409a8a143be959307efe'))

    def test_content_property_google_case3(self):
        if WORK_ENVIRONMENT: return
        test_data = 'https://www.google.com/maps/place/Han+Ha+Rum+Korean+Restaurant/@22.3636765,113.4067433,9z/data=!4m8!1m2!2m1!1z7Iud64u5!3m4!1s0x34040056de2d51b3:0xae100fb893526bdf!8m2!3d22.2801408!4d114.182783'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], 'google')
        saved = LegacyPlace.objects.first()
        self.assertEqual(lp.content, 'ChIJs1Et3lYABDQR32tSk7gPEK4.google')
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('ba698d72-72bb-1a1e-97bb-3c44f54b973f'))

    def test_content_property_kakao_case1(self):
        test_data = '14720610.kakao'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
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
        test_data = 'https://place.kakao.com/places/14720610/홍콩'
        normalized_test_data = '14720610.kakao'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], 'kakao')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000004-0000-0000-0000-000014720610'))

    def test_content_property_kakao_case3(self):
        test_data = 'http://place.kakao.com/places/14720610'
        normalized_test_data = '14720610.kakao'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], 'kakao')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000004-0000-0000-0000-000014720610'))

    def test_content_property_kakao_case4(self):
        test_data = 'http://m.map.daum.net/actions/detailInfoView?id=15493954'
        normalized_test_data = '15493954.kakao'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], 'kakao')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000004-0000-0000-0000-000015493954'))

    def test_content_property_mango_case1(self):
        test_data = 'https://www.mangoplate.com/restaurants/f-YvkBx8IemC'
        normalized_test_data = 'f-YvkBx8IemC.mango'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        self.assertEqual(lp.uuid.split('.')[1], 'mango')
        saved = LegacyPlace.objects.first()
        self.assertNotEqual(lp.content, test_data)
        self.assertEqual(lp.content, normalized_test_data)
        self.assertEqual(saved, lp)
        self.assertEqual(saved.id, lp.id)
        self.assertEqual(saved.content, lp.content)
        self.assertEqual(saved.id, UUID('00000005-662d-5976-6b42-783849656d43'))

    def test_access_by_4square(self):
        if WORK_ENVIRONMENT: return
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        path = Path(lp.path_accessed)
        if path.exists():
            path.unlink()
        self.assertEqual(path.exists(), False)
        lp.access_force()
        self.assertEqual(path.exists(), True)

    def _skip_test_access_by_naver(self):
        test_data = '21149144.naver'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        path = Path(lp.path_accessed)
        if path.exists():
            path.unlink()
        self.assertEqual(path.exists(), False)
        lp.access()
        self.assertEqual(path.exists(), True)

    def test_access_by_kakao(self):
        test_data = '14720610.kakao'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        path = Path(lp.path_accessed)
        if path.exists():
            path.unlink()
        self.assertEqual(path.exists(), False)
        lp.access()
        self.assertEqual(path.exists(), True)

    def test_access_by_mango(self):
        test_data = 'f-YvkBx8IemC.mango'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        path = Path(lp.path_accessed)
        if path.exists():
            path.unlink()
        self.assertEqual(path.exists(), False)
        lp.access()
        self.assertEqual(path.exists(), True)

    def test_access_by_google(self):
        if WORK_ENVIRONMENT: return
        test_data = 'ChIJs1Et3lYABDQR32tSk7gPEK4.google'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
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
        lp, is_created = LegacyPlace.get_or_create_smart('14720610.kakao')
        self.assertEqual(LegacyPlace.objects.count(), 1)
        self.assertEqual(lp.place, None)
        self.assertEqual(lp.lp_type, LP_TYPE['kakao'])

        lp2, is_created = LegacyPlace.get_or_create_smart('14720610.kakao')
        self.assertEqual(LegacyPlace.objects.count(), 1)
        self.assertEqual(lp2.place, None)
        self.assertEqual(lp2.lp_type, LP_TYPE['kakao'])
        self.assertEqual(lp2, lp)

        lp3, is_created = LegacyPlace.get_or_create_smart('15738374.kakao')
        self.assertEqual(LegacyPlace.objects.count(), 2)
        self.assertEqual(lp3.place, None)
        self.assertEqual(lp3.lp_type, LP_TYPE['kakao'])
        self.assertNotEqual(lp3, lp)

        lp.place = place
        lp.save()
        self.assertEqual(place.lps.first(), lp)

        lp3.place = place
        with self.assertRaises(IntegrityError):
            lp3.save()

    def test_get_from_url(self):
        # naver disabled
        '''
        url, is_created = Url.get_or_create_smart('http://map.naver.com/local/siteview.nhn?code=21149144')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '21149144.naver')

        url, is_created = Url.get_or_create_smart('http://map.naver.com/?app=Y&version=10&appMenu=location&pinId=31130096&pinType=site&lat=37.3916387&lng=127.0584149&title=능이향기&dlevel=11')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '31130096.naver')

        url, is_created = Url.get_or_create_smart('http://m.store.naver.com/restaurants/detail?id=37333252')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '37333252.naver')

        url, is_created = Url.get_or_create_smart('http://m.map.naver.com/siteview.nhn?code=31176899')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '31176899.naver')

        url, is_created = Url.get_or_create_smart('https://m.map.naver.com/viewer/map.nhn?pinType=site&pinId=21652462')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '21652462.naver')

        url, is_created = Url.get_or_create_smart('https://m.map.naver.com/siteview.nhn?code=11523188&ret_url=https%3A%2F%2Fm.search.naver.com%2Fsearch.naver%3Fwhere%3Dm%26query%3D%25EC%259C%2584%25EB%258B%25B4%25ED%2595%259C%25EB%25B0%25A9%25EB%25B3%2591%25EC%259B%2590%26sm%3Dmsv_nex%23m_local')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '11523188.naver')
        '''


        url, is_created = Url.get_or_create_smart('http://place.kakao.com/places/14720610')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '14720610.kakao')

        url, is_created = Url.get_or_create_smart('http://m.map.daum.net/actions/detailInfoView?id=15493954')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '15493954.kakao')

        url, is_created = Url.get_or_create_smart('http://m.map.daum.net/actions/detailInfoView?id=15493954')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '15493954.kakao')

        url, is_created = Url.get_or_create_smart('http://place.map.daum.net/26799590')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '26799590.kakao')

        url, is_created = Url.get_or_create_smart('http://foursquare.com/v/4ccffc63f6378cfaace1b1d6')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '4ccffc63f6378cfaace1b1d6.4square')

        url, is_created = Url.get_or_create_smart('https://ko.foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '4ccffc63f6378cfaace1b1d6.4square')

        url, is_created = Url.get_or_create_smart('http://ko.foursquare.com/v/4ccffc63f6378cfaace1b1d6')
        self.assertEqual(LegacyPlace.get_from_url(url).content, '4ccffc63f6378cfaace1b1d6.4square')

        url, is_created = Url.get_or_create_smart('https://www.mangoplate.com/restaurants/f-YvkBx8IemC')
        self.assertEqual(LegacyPlace.get_from_url(url).content, 'f-YvkBx8IemC.mango')

        if not WORK_ENVIRONMENT:
            url, is_created = Url.get_or_create_smart('https://www.google.com/maps/place/Han+Ha+Rum+Korean+Restaurant/@22.3636765,113.4067433,9z/data=!4m8!1m2!2m1!1z7Iud64u5!3m4!1s0x34040056de2d51b3:0xae100fb893526bdf!8m2!3d22.2801408!4d114.182783')
            self.assertEqual(LegacyPlace.get_from_url(url).content, 'ChIJs1Et3lYABDQR32tSk7gPEK4.google')

    def test_access_methods(self):
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)

        lp.access()
        self.assertValidLocalFile(lp.path_accessed)
        self.assertValidInternetUrl(lp.url_accessed)

    def test_summarize_methods(self):
        test_data = '14720610.kakao'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)

        lp.summarize()
        self.assertValidLocalFile(lp.path_summarized)
        self.assertValidInternetUrl(lp.url_summarized)

    def _skip_test_content_summarized_by_naver(self):
        test_data = '21149144.naver'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        lp.summarize()
        pb = lp.content_summarized
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, '방아깐')
        self.assertIn(pb.images[0].content, [
            unquote_plus('https://ssl.map.naver.com/staticmap/image?version=1.1&crs=EPSG%3A4326&caller=og_map&center=127.092557%2C37.390271&level=11&scale=2&w=500&h=500&markers=type%2Cdefault2%2C127.092557%2C37.390271&baselayer=default'),
            'http://ldb.phinf.naver.net/20150901_174/1441078320814Nj4Fe_JPEG/146466556151173_0.jpeg',
        ])
        self.assertValidLocalFile(pb.images[0].path_summarized)
        self.assertValidInternetUrl(pb.images[0].url_summarized)

    def test_content_summarized_by_kakao(self):
        test_data = '14720610.kakao'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        lp.summarize()
        pb = lp.content_summarized
        self.printJson(pb)
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, '홍콩')
        self.assertEqual(pb.images[0].content, unquote_plus(
            'http://img1.daumcdn.net/thumb/C300x300/?fname=http%3A%2F%2Fdn-rp-place.kakao.co.kr%2Fplace%2FoWaiTZmpy7%2FviOeK5KRQK7mEsAHlckFgK%2FapreqCwxgnM_l.jpg'
        ))
        self.assertValidLocalFile(pb.images[0].path_summarized)
        self.assertValidInternetUrl(pb.images[0].url_summarized)

    def test_content_summarized_by_4square(self):
        if WORK_ENVIRONMENT: return
        test_data = '4ccffc63f6378cfaace1b1d6.4square'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        lp.summarize()
        pb = lp.content_summarized
        self.printJson(pb)
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, '방아깐')
        self.assertEqual(pb.images[0].content, unquote_plus(
            'https://irs0.4sqi.net/img/general/720x537/13818664_F1SNp5hPhsRBn4qksbkmBCIXv7gsSbOuTXbb3tX8ZG4.jpg'
        ))
        self.assertValidLocalFile(pb.images[0].path_summarized)
        self.assertValidInternetUrl(pb.images[0].url_summarized)

    def test_content_summarized_by_4square2(self):
        if WORK_ENVIRONMENT: return
        test_data = '40a55d80f964a52020f31ee3.4square'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        lp.summarize()
        pb = lp.content_summarized
        self.printJson(pb)
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, 'Clinton St. Baking Co. & Restaurant')
        self.assertEqual(pb.images[0].content, unquote_plus(
            'https://irs2.4sqi.net/img/general/612x612/690170_HnduV5yM9RLNUHQseOOvDi3OCm4AoYmMld79iVTxrPg.jpg'
        ))
        self.assertValidLocalFile(pb.images[0].path_summarized)
        self.assertValidInternetUrl(pb.images[0].url_summarized)

    def test_content_summarized_by_mango(self):
        test_data = 'f-YvkBx8IemC.mango'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        lp.summarize()
        pb = lp.content_summarized
        self.printJson(pb)
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, '제로투나인')
        self.assertEqual(pb.images[0].content, unquote_plus(
            'https://mp-seoul-image-production-s3.mangoplate.com/259736/xverhn9edfxp5w.jpg'
        ))
        self.assertValidLocalFile(pb.images[0].path_summarized)
        self.assertValidInternetUrl(pb.images[0].url_summarized)

    def test_content_summarized_by_google(self):
        if WORK_ENVIRONMENT: return
        test_data = 'ChIJs1Et3lYABDQR32tSk7gPEK4.google'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        lp.summarize()
        pb = lp.content_summarized
        self.printJson(pb)
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, 'Han Ha Rum Korean Restaurant')
        self.assertEqual(pb.phone.content, '+85228666927')
        self.assertEqual(pb.addr.content, 'Causeway Bay Plaza 1, 489 Hennessy Rd, Causeway Bay, Hong Kong')
        self.assertValidLocalFile(pb.images[0].path_summarized)
        self.assertValidInternetUrl(pb.images[0].url_summarized)


class PhoneNumberTest(APITestBase):

    def test_string_representation(self):
        test_data = '+821055979245'
        phone, is_created = PhoneNumber.get_or_create_smart(test_data)
        self.assertEqual(unicode(phone), test_data)

    def test_save_and_retreive(self):
        test_data = '+82 10-5597-9245'
        phone, is_created = PhoneNumber.get_or_create_smart(test_data)
        saved = PhoneNumber.objects.first()
        self.assertEqual(phone.uuid, '%s.phone' % b16encode(phone.id.bytes))
        self.assertEqual(saved, phone)
        self.assertEqual(saved.id, phone.id)
        saved2 = PhoneNumber.get_from_json('{"uuid": "%s", "content": null}' % phone.uuid)
        self.assertEqual(saved2, phone)
        saved3 = PhoneNumber.get_from_json('{"uuid": null, "content": "%s"}' % phone.content)
        self.assertEqual(saved3, phone)

    def test_content_property(self):
        test_data = '010-5597-9245'
        phone, is_created = PhoneNumber.get_or_create_smart(test_data)
        saved = PhoneNumber.objects.first()
        normalized_data = PhoneNumber.normalize_content(test_data)
        self.assertEqual(phone.content, normalized_data)
        self.assertEqual(saved, phone)
        self.assertEqual(saved.id, phone.id)
        self.assertEqual(saved.content, phone.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        test_data = '031-724-2733'
        phone, is_created = PhoneNumber.get_or_create_smart(test_data)

        path = Path(phone.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        phone.access_force()
        self.assertEqual(path.exists(), True)


class PlaceNameTest(APITestBase):

    def test_string_representation(self):
        test_data = '방아깐'
        pname, is_created = PlaceName.get_or_create_smart(test_data)
        self.assertEqual(unicode(pname), test_data)

    def test_save_and_retreive(self):
        test_data = '방아깐'
        pname, is_created = PlaceName.get_or_create_smart(test_data)
        saved = PlaceName.objects.first()
        self.assertEqual(pname.uuid, '%s.pname' % b16encode(pname.id.bytes))
        self.assertEqual(saved, pname)
        self.assertEqual(saved.id, pname.id)
        saved2 = PlaceName.get_from_json('{"uuid": "%s", "content": null}' % pname.uuid)
        self.assertEqual(saved2, pname)
        saved3 = PlaceName.get_from_json('{"uuid": null, "content": "%s"}' % pname.content)
        self.assertEqual(saved3, pname)

    def test_content_property(self):
        test_data = '방아깐'
        pname, is_created = PlaceName.get_or_create_smart(test_data)
        saved = PlaceName.objects.first()
        self.assertEqual(pname.content, test_data)
        self.assertEqual(saved, pname)
        self.assertEqual(saved.id, pname.id)
        self.assertEqual(saved.content, pname.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        test_data = '방아깐'
        pname, is_created = PlaceName.get_or_create_smart(test_data)

        path = Path(pname.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        pname.access_force()
        self.assertEqual(path.exists(), True)


class AddressTest(APITestBase):

    def test_string_representation(self):
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr, is_created = Address.get_or_create_smart(test_data)
        self.assertEqual(unicode(addr), test_data)

    def test_save_and_retreive(self):
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr, is_created = Address.get_or_create_smart(test_data)
        saved = Address.objects.first()
        self.assertEqual(addr.uuid, '%s.addr' % b16encode(addr.id.bytes))
        self.assertEqual(saved, addr)
        self.assertEqual(saved.id, addr.id)
        saved2 = Address.get_from_json('{"uuid": "%s", "content": null}' % addr.uuid)
        self.assertEqual(saved2, addr)
        saved3 = Address.get_from_json('{"uuid": null, "content": "%s"}' % addr.content)
        self.assertEqual(saved3, addr)

    def test_content_property(self):
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr, is_created = Address.get_or_create_smart(test_data)
        saved = Address.objects.first()
        self.assertEqual(addr.content, test_data)
        self.assertEqual(saved, addr)
        self.assertEqual(saved.id, addr.id)
        self.assertEqual(saved.content, addr.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr, is_created = Address.get_or_create_smart(test_data)

        path = Path(addr.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        addr.access_force()
        self.assertEqual(path.exists(), True)


class PlaceNoteTest(APITestBase):

    def test_string_representation(self):
        test_data = '능이백숙 국물 죽이네~ ㅎㅎ'
        pnote, is_created = PlaceNote.get_or_create_smart(test_data)
        self.assertEqual(unicode(pnote), test_data)

    def test_save_and_retreive(self):
        test_data = '능이백숙 국물 죽이네~ ㅎㅎ'
        pnote, is_created = PlaceNote.get_or_create_smart(test_data)
        saved = PlaceNote.objects.first()
        self.assertEqual(pnote.uuid, '%s.pnote' % b16encode(pnote.id.bytes))
        self.assertEqual(saved, pnote)
        self.assertEqual(saved.id, pnote.id)
        saved2 = PlaceNote.get_from_json('{"uuid": "%s", "content": null}' % pnote.uuid)
        self.assertEqual(saved2, pnote)
        saved3 = PlaceNote.get_from_json('{"uuid": null, "content": "%s"}' % pnote.content)
        self.assertEqual(saved3, pnote)

    def test_content_property(self):
        test_data = '능이백숙 국물 죽이네~ ㅎㅎ'
        pnote, is_created = PlaceNote.get_or_create_smart(test_data)
        saved = PlaceNote.objects.first()
        self.assertEqual(pnote.content, test_data)
        self.assertEqual(saved, pnote)
        self.assertEqual(saved.id, pnote.id)
        self.assertEqual(saved.content, pnote.content)

    def test_content_for_search(self):
        test_data = '#여의도 #중소기업중앙회 #블로터미디어 #콘텐츠마케팅 #컨퍼런스 #72초티비 #피키캐스트 # 메이크어스 #ㅍㅍㅅㅅ'
        pnote, is_created = PlaceNote.get_or_create_smart(test_data)
        self.assertEqual(pnote.content_for_search, '여의도 중소기업중앙회 블로터미디어 콘텐츠마케팅 컨퍼런스 72초티비 피키캐스트  메이크어스 ㅍㅍㅅㅅ')

    def test_cjson(self):
        test_data = '능이백숙 국물 죽이네~ ㅎㅎ'
        pnote, is_created = PlaceNote.get_or_create_smart(test_data)
        pnote.timestamp = 1
        self.assertIn('timestamp', pnote.cjson)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        test_data = '능이백숙 국물 죽이네~ ㅎㅎ'
        pnote, is_created = PlaceNote.get_or_create_smart(test_data)

        path = Path(pnote.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        pnote.access_force()
        self.assertEqual(path.exists(), True)


class ImageNoteTest(APITestBase):

    def test_string_representation(self):
        test_data = '자기랑 진우랑 찰칵~ ^^'
        inote, is_created = ImageNote.get_or_create_smart(test_data)
        self.assertEqual(unicode(inote), test_data)

    def test_save_and_retreive(self):
        test_data = '자기랑 진우랑 찰칵~ ^^'
        inote, is_created = ImageNote.get_or_create_smart(test_data)
        saved = ImageNote.objects.first()
        self.assertEqual(inote.uuid, '%s.inote' % b16encode(inote.id.bytes))
        self.assertEqual(saved, inote)
        self.assertEqual(saved.id, inote.id)
        saved2 = ImageNote.get_from_json('{"uuid": "%s", "content": null}' % inote.uuid)
        self.assertEqual(saved2, inote)
        saved3 = ImageNote.get_from_json('{"uuid": null, "content": "%s"}' % inote.content)
        self.assertEqual(saved3, inote)

    def test_content_property(self):
        test_data = '자기랑 진우랑 찰칵~ ^^'
        inote, is_created = ImageNote.get_or_create_smart(test_data)
        saved = ImageNote.objects.first()
        self.assertEqual(inote.content, test_data)
        self.assertEqual(saved, inote)
        self.assertEqual(saved.id, inote.id)
        self.assertEqual(saved.content, inote.content)

    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        test_data = '자기랑 진우랑 찰칵~ ^^'
        inote, is_created = ImageNote.get_or_create_smart(test_data)

        path = Path(inote.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        inote.access_force()
        self.assertEqual(path.exists(), True)


class TagNameTest(APITestBase):

    def test_string_representation(self):
        test_data = '관심'
        tname, is_created = TagName.get_or_create_smart(test_data)
        self.assertEqual(unicode(tname), test_data)

    def test_save_and_retreive(self):
        test_data = '관심'
        tname, is_created = TagName.get_or_create_smart(test_data)
        saved = TagName.objects.first()
        self.assertEqual(tname.uuid, '%s.tname' % b16encode(tname.id.bytes))
        self.assertEqual(saved, tname)
        self.assertEqual(saved.id, tname.id)
        saved2 = TagName.get_from_json('{"uuid": "%s", "content": null}' % tname.uuid)
        self.assertEqual(saved2, tname)
        saved3 = TagName.get_from_json('{"uuid": null, "content": "%s"}' % tname.content)
        self.assertEqual(saved3, tname)

    def test_content_property(self):
        test_data = '관심'
        tname, is_created = TagName.get_or_create_smart(test_data)
        saved = TagName.objects.first()
        self.assertEqual(tname.content, test_data)
        self.assertEqual(saved, tname)
        self.assertEqual(saved.id, tname.id)
        self.assertEqual(saved.content, tname.content)

    def test_remove_tag_name(self):
        test_data = '관심'
        tname, is_created = TagName.get_or_create_smart(test_data)
        test_data2 = '-관심'
        tname2, is_created2 = TagName.get_or_create_smart(test_data2)
        self.assertEqual(tname.is_remove, False)
        self.assertEqual(tname2.is_remove, True)
        self.assertEqual(tname.remove_target, None)
        self.assertEqual(tname2.remove_target, tname)


    # TODO : 구글검색도 땡겨올 수 있도록 수정 후 부활
    def __skip__test_access_methods(self):
        test_data = '관심'
        tname, is_created = TagName.get_or_create_smart(test_data)

        path = Path(tname.path_accessed)
        if path.exists():
            path.unlink()

        self.assertEqual(path.exists(), False)
        tname.access_force()
        self.assertEqual(path.exists(), True)
