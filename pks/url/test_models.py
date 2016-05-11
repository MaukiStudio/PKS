#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.db import IntegrityError
from base64 import b16encode

from base.tests import APITestBase
from url.models import Url


class UrlTest(APITestBase):

    def test_string_representation(self):
        url = Url()
        url.content = 'http://www.naver.com/'
        self.assertEqual(unicode(url), url.content)

    def test_save_and_retreive(self):
        url = Url()
        url.content = 'http://www.naver.com/'
        url.save()
        saved = Url.objects.first()
        self.assertEqual(url.uuid, '%s.url' % b16encode(url.id.bytes))
        self.assertEqual(saved, url)
        self.assertEqual(saved.id, url.id)
        saved2 = Url.get_from_json('{"uuid": "%s", "content": null}' % url.uuid)
        self.assertEqual(saved2, url)
        saved3 = Url.get_from_json('{"uuid": null, "content": "%s"}' % url.content)
        self.assertEqual(saved3, url)

    def test_content_property(self):
        url = Url()
        test_value = 'http://www.naver.com/'
        url.content = test_value
        url.save()
        saved = Url.objects.first()
        self.assertEqual(saved.content, test_value)

        url2 = Url()
        url2.content = url.content
        self.assertEqual(1, Url.objects.count())
        url.save()
        self.assertEqual(1, Url.objects.count())

        with self.assertRaises(IntegrityError):
            Url.objects.create(content=url.content)

    def test_access_methods(self):
        url = Url()
        test_data = 'http://m.blog.naver.com/mardukas/220555109681'
        url.content = test_data
        url.save()

        url.access()
        self.assertValidLocalFile(url.path_accessed)
        self.assertValidInternetUrl(url.url_accessed)

    def test_naver_shortener_url1(self):
        url = Url()
        test_value = 'http://me2.do/GZkw1y27'
        normalized_value = 'http://map.naver.com/?app=Y&version=10&appMenu=location&pinId=31130096&pinType=site&lat=37.3916387&lng=127.0584149&title=%EB%8A%A5%EC%9D%B4%ED%96%A5%EA%B8%B0&dlevel=11'
        url.content = test_value
        self.assertEqual(Url.objects.count(), 0)
        url.save()
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)

    def test_naver_shortener_url2(self):
        url = Url()
        test_value = 'http://me2.do/xLOGJZ19'
        normalized_value = 'http://m.store.naver.com/restaurants/detail?id=37333252'
        url.content = test_value
        self.assertEqual(Url.objects.count(), 0)
        url.save()
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)

    def test_naver_shortener_url3(self):
        url = Url()
        test_value = 'http://me2.do/xgcFeqMZ'
        normalized_value = 'http://m.map.naver.com/siteview.nhn?code=31176899'
        url.content = test_value
        self.assertEqual(Url.objects.count(), 0)
        url.save()
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)

    def test_naver_shortener_url4(self):
        url = Url()
        test_value = 'http://me2.do/GNAl9bvK'
        normalized_value = 'http://blog.naver.com/a878062/220392611381'
        url.content = test_value
        self.assertEqual(Url.objects.count(), 0)
        url.save()
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)

    def test_naver_shortener_url_with_garbage(self):
        url = Url()
        test_value = '''
            [네이버 지도]
            능이향기
            031-8017-9092
            경기도 성남시 분당구 하오개로 353
            http://me2.do/GZkw1y27
            업체명 : 능이향기
        '''
        normalized_value = 'http://map.naver.com/?app=Y&version=10&appMenu=location&pinId=31130096&pinType=site&lat=37.3916387&lng=127.0584149&title=%EB%8A%A5%EC%9D%B4%ED%96%A5%EA%B8%B0&dlevel=11'
        url.content = test_value
        self.assertEqual(Url.objects.count(), 0)
        url.save()
        self.assertEqual(Url.objects.count(), 1)
        saved = Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)

    def test_encoded_url1(self):
        test_data1 = 'https://place.kakao.com/places/10972091/%ED%99%8D%EB%AA%85'
        test_data2 = 'https://place.kakao.com/places/10972091/홍명'

        self.assertEqual(Url.objects.count(), 0)
        url1 = Url.get_from_json('{"content": "%s"}' % test_data1)
        self.assertEqual(Url.objects.count(), 1)
        url2 = Url.get_from_json('{"content": "%s"}' % test_data2)
        self.assertEqual(Url.objects.count(), 1)
        self.assertEqual(url1, url2)

    def test_encoded_url2(self):
        test_data2 = 'https://place.kakao.com/places/10972091/%ED%99%8D%EB%AA%85'
        test_data1 = 'https://place.kakao.com/places/10972091/홍명'

        self.assertEqual(Url.objects.count(), 0)
        url1 = Url.get_from_json('{"content": "%s"}' % test_data1)
        self.assertEqual(Url.objects.count(), 1)
        url2 = Url.get_from_json('{"content": "%s"}' % test_data2)
        self.assertEqual(Url.objects.count(), 1)
        self.assertEqual(url1, url2)
