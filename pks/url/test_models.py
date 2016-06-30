#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.db import IntegrityError
from base64 import b16encode
from urllib import unquote_plus

from base.tests import APITestBase
from url.models import Url, UrlPlaceRelation
from pks.settings import WORK_ENVIRONMENT
from place.models import Place


class UrlTest(APITestBase):

    def test_string_representation(self):
        url, is_created = Url.get_or_create_smart('http://www.naver.com/')
        self.assertEqual(unicode(url), url.content)

    def test_save_and_retreive(self):
        url, is_created = Url.get_or_create_smart('http://www.naver.com/')
        saved = Url.objects.first()
        self.assertEqual(url.uuid, '%s.url' % b16encode(url.id.bytes))
        self.assertEqual(saved, url)
        self.assertEqual(saved.id, url.id)
        saved2 = Url.get_from_json('{"uuid": "%s", "content": null}' % url.uuid)
        self.assertEqual(saved2, url)
        saved3 = Url.get_from_json('{"uuid": null, "content": "%s"}' % url.content)
        self.assertEqual(saved3, url)

    def test_content_property(self):
        test_value = 'http://www.naver.com/'
        url, is_created = Url.get_or_create_smart(test_value)
        saved = Url.objects.first()
        self.assertEqual(saved.content, test_value)

        self.assertEqual(1, Url.objects.count())
        Url.get_or_create_smart(test_value)
        self.assertEqual(1, Url.objects.count())

        with self.assertRaises(IntegrityError):
            Url.objects.create(content=url.content)

    def test_access_methods(self):
        test_data = 'http://m.blog.naver.com/mardukas/220555109681'
        url, is_created = Url.get_or_create_smart(test_data)

        url.access()
        self.assertValidLocalFile(url.path_accessed)
        self.assertValidInternetUrl(url.url_accessed)

    def test_naver_shortener_url1(self):
        test_value = 'http://me2.do/GZkw1y27'
        normalized_value = 'http://map.naver.com/?app=Y&version=10&appMenu=location&pinId=31130096&pinType=site&lat=37.3916387&lng=127.0584149&title=%EB%8A%A5%EC%9D%B4%ED%96%A5%EA%B8%B0&dlevel=11'
        self.assertEqual(Url.objects.count(), 0)
        url, is_created = Url.get_or_create_smart(test_value)
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, unquote_plus(normalized_value.encode('utf-8')).decode('utf-8'))
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, unquote_plus(normalized_value.encode('utf-8')).decode('utf-8'))

    def test_naver_shortener_url2(self):
        test_value = 'http://me2.do/xLOGJZ19'
        normalized_value = 'http://m.store.naver.com/restaurants/detail?id=37333252'
        self.assertEqual(Url.objects.count(), 0)
        url, is_created = Url.get_or_create_smart(test_value)
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)

    def test_naver_shortener_url3(self):
        test_value = 'http://me2.do/xgcFeqMZ'
        normalized_value = 'http://m.map.naver.com/siteview.nhn?code=31176899'
        self.assertEqual(Url.objects.count(), 0)
        url, is_created = Url.get_or_create_smart(test_value)
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)

    def test_naver_shortener_url4(self):
        test_value = 'http://me2.do/GNAl9bvK'
        normalized_value = 'http://blog.naver.com/a878062/220392611381'
        self.assertEqual(Url.objects.count(), 0)
        url, is_created = Url.get_or_create_smart(test_value)
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)

    def test_naver_shortener_url_with_garbage(self):
        test_value = '''
            [네이버 지도]
            능이향기
            031-8017-9092
            경기도 성남시 분당구 하오개로 353
            http://me2.do/GZkw1y27
            업체명 : 능이향기
        '''
        normalized_value = 'http://map.naver.com/?app=Y&version=10&appMenu=location&pinId=31130096&pinType=site&lat=37.3916387&lng=127.0584149&title=%EB%8A%A5%EC%9D%B4%ED%96%A5%EA%B8%B0&dlevel=11'
        self.assertEqual(Url.objects.count(), 0)
        url, is_created = Url.get_or_create_smart(test_value)
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, unquote_plus(normalized_value.encode('utf-8')).decode('utf-8'))
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, unquote_plus(normalized_value.encode('utf-8')).decode('utf-8'))

    def test_4square_shortener_url(self):
        if WORK_ENVIRONMENT: return
        test_value = 'http://4sq.com/MVWRaG'
        normalized_value = 'https://foursquare.com/v/doredore-도레도레/500d3737e4b03e92379f2714'
        self.assertEqual(Url.objects.count(), 0)
        url, is_created = Url.get_or_create_smart(test_value)
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)

    def test_4square_shortener_url_with_garbage(self):
        if WORK_ENVIRONMENT: return
        test_value = 'DOREDORE (도레도레) - 하남대로 929 - http://4sq.com/MVWRaG'
        normalized_value = 'https://foursquare.com/v/doredore-도레도레/500d3737e4b03e92379f2714'
        self.assertEqual(Url.objects.count(), 0)
        url, is_created = Url.get_or_create_smart(test_value)
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, unquote_plus(normalized_value.encode('utf-8')).decode('utf-8'))
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, unquote_plus(normalized_value.encode('utf-8')).decode('utf-8'))

    def test_encoded_url1(self):
        test_data1 = 'https://place.kakao.com/places/10972091/%ED%99%8D%EB%AA%85'
        test_data2 = 'https://place.kakao.com/places/10972091/홍명'

        self.assertEqual(Url.objects.count(), 0)
        url1, is_created = Url.get_or_create_smart(test_data1)
        self.assertEqual(Url.objects.count(), 1)
        url2, is_created = Url.get_or_create_smart(test_data2)
        self.assertEqual(Url.objects.count(), 1)
        self.assertEqual(url1, url2)
        self.assertEqual(url1.content, url2.content)

    def test_encoded_url2(self):
        test_data2 = 'https://place.kakao.com/places/10972091/%ED%99%8D%EB%AA%85'
        test_data1 = 'https://place.kakao.com/places/10972091/홍명'

        self.assertEqual(Url.objects.count(), 0)
        url1, is_created = Url.get_or_create_smart(test_data1)
        self.assertEqual(Url.objects.count(), 1)
        url2, is_created = Url.get_or_create_smart(test_data2)
        self.assertEqual(Url.objects.count(), 1)
        self.assertEqual(url1, url2)
        self.assertEqual(url1.content, url2.content)

    def test_encoded_url3(self):
        test_data1 = 'https://m.map.naver.com/siteview.nhn?code=11523188&ret_url=https%3A%2F%2Fm.search.naver.com%2Fsearch.naver%3Fwhere%3Dm%26query%3D%25EC%259C%2584%25EB%258B%25B4%25ED%2595%259C%25EB%25B0%25A9%25EB%25B3%2591%25EC%259B%2590%26sm%3Dmsv_nex%23m_local'
        test_data2 = 'https://m.map.naver.com/siteview.nhn?code=11523188&ret_url=https://m.search.naver.com/search.naver?where=m&query=위담한방병원&sm=msv_nex#m_local'

        self.assertEqual(Url.objects.count(), 0)
        url1, is_created = Url.get_or_create_smart(test_data1)
        self.assertEqual(Url.objects.count(), 1)
        url2, is_created = Url.get_or_create_smart(test_data2)
        self.assertEqual(Url.objects.count(), 1)
        self.assertEqual(url1, url2)
        self.assertEqual(url1.content, url2.content)

    def test_encoded_url4(self):
        test_data2 = 'https://m.map.naver.com/siteview.nhn?code=11523188&ret_url=https%3A%2F%2Fm.search.naver.com%2Fsearch.naver%3Fwhere%3Dm%26query%3D%25EC%259C%2584%25EB%258B%25B4%25ED%2595%259C%25EB%25B0%25A9%25EB%25B3%2591%25EC%259B%2590%26sm%3Dmsv_nex%23m_local'
        test_data1 = 'https://m.map.naver.com/siteview.nhn?code=11523188&ret_url=https://m.search.naver.com/search.naver?where=m&query=위담한방병원&sm=msv_nex#m_local'

        self.assertEqual(Url.objects.count(), 0)
        url1, is_created = Url.get_or_create_smart(test_data1)
        self.assertEqual(Url.objects.count(), 1)
        url2, is_created = Url.get_or_create_smart(test_data2)
        self.assertEqual(Url.objects.count(), 1)
        self.assertEqual(url1, url2)
        self.assertEqual(url1.content, url2.content)


class UrlPlaceRelationTest(APITestBase):

    def setUp(self):
        super(UrlPlaceRelationTest, self).setUp()
        self.url = Url.objects.create(content='http://www.naver.com/')
        self.place = Place.objects.create()
        self.upr = UrlPlaceRelation(url=self.url, place=self.place)

    def test_save_and_retrieve(self):
        self.assertEqual(UrlPlaceRelation.objects.count(), 0)
        self.upr.save()
        self.assertEqual(UrlPlaceRelation.objects.count(), 1)
        saved = UrlPlaceRelation.objects.first()
        self.assertEqual(saved, self.upr)
        self.assertEqual(saved.url, self.url)
        self.assertEqual(saved.place, self.place)

    def test_unique(self):
        self.upr.save()
        other = UrlPlaceRelation(url=self.url, place=self.place)
        with self.assertRaises(IntegrityError):
            other.save()
