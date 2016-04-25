#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.db import IntegrityError
from base64 import b16encode

from base.tests import APITestBase
from url import models


class UrlTest(APITestBase):

    def test_string_representation(self):
        url = models.Url()
        url.content = 'http://www.maukistudio.com/'
        self.assertEqual(unicode(url), url.content)

    def test_save_and_retreive(self):
        url = models.Url()
        url.content = 'http://www.maukistudio.com/'
        url.save()
        saved = models.Url.objects.first()
        self.assertEqual(url.uuid, '%s.url' % b16encode(url.id.bytes))
        self.assertEqual(saved, url)
        self.assertEqual(saved.id, url.id)
        saved2 = models.Url.get_from_json('{"uuid": "%s", "content": null}' % url.uuid)
        self.assertEqual(saved2, url)
        saved3 = models.Url.get_from_json('{"uuid": null, "content": "%s"}' % url.content)
        self.assertEqual(saved3, url)

    def test_content_property(self):
        url = models.Url()
        test_value = 'http://www.maukistudio.com/'
        url.content = test_value
        url.save()
        saved = models.Url.objects.first()
        self.assertEqual(saved.content, test_value)

        url2 = models.Url()
        url2.content = url.content
        self.assertEqual(1, models.Url.objects.count())
        url.save()
        self.assertEqual(1, models.Url.objects.count())

        with self.assertRaises(IntegrityError):
            models.Url.objects.create(content=url.content)

    def test_access_methods(self):
        url = models.Url()
        test_data = 'http://m.blog.naver.com/mardukas/220555109681'
        url.content = test_data
        url.save()

        url.access()
        self.assertValidLocalFile(url.path_accessed)
        self.assertValidInternetUrl(url.url_accessed)

    def test_summarize_methods(self):
        url = models.Url()
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        url.content = test_data
        url.save()

        url.summarize()
        self.assertValidLocalFile(url.path_summarized)
        self.assertValidInternetUrl(url.url_summarized)

    def test_content_summarized_by_naver(self):
        url = models.Url()
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        url.content = test_data
        url.save()
        url.summarize()
        pb = url.content_summarized
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, '방아깐')

    def test_content_summarized_by_kakao(self):
        url = models.Url()
        test_data = 'http://place.kakao.com/places/14720610'
        url.content = test_data
        url.save()
        url.summarize()
        pb = url.content_summarized
        self.printJson(pb)
        self.assertEqual(pb.is_valid(), True)
        self.assertEqual(pb.name.content, '홍콩')

    def test_naver_shortener_url1(self):
        url = models.Url()
        test_value = 'http://me2.do/GZkw1y27'
        normalized_value = 'http://map.naver.com/local/siteview.nhn?code=31130096'
        url.content = test_value
        self.assertEqual(models.Url.objects.count(), 0)
        url.save()
        self.assertEqual(models.Url.objects.count(), 1)
        saved = models.Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)
        url.summarize()
        pb = url.content_summarized
        self.assertEqual(pb.is_valid(), True)

    def test_naver_shortener_url2(self):
        url = models.Url()
        test_value = 'http://me2.do/xLOGJZ19'
        normalized_value = 'http://map.naver.com/local/siteview.nhn?code=37333252'
        url.content = test_value
        self.assertEqual(models.Url.objects.count(), 0)
        url.save()
        self.assertEqual(models.Url.objects.count(), 1)
        saved = models.Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)
        url.summarize()
        pb = url.content_summarized
        self.assertEqual(pb.is_valid(), True)

    def test_naver_shortener_url_with_garbage(self):
        url = models.Url()
        test_value = '''
            [네이버 지도]
            능이향기
            031-8017-9092
            경기도 성남시 분당구 하오개로 353
            http://me2.do/GZkw1y27
        '''
        normalized_value = 'http://map.naver.com/local/siteview.nhn?code=31130096'
        url.content = test_value
        self.assertEqual(models.Url.objects.count(), 0)
        url.save()
        self.assertEqual(models.Url.objects.count(), 1)
        saved = models.Url.objects.first()
        self.assertEqual(url.content, normalized_value)
        self.assertEqual(saved, url)
        self.assertEqual(saved.content, normalized_value)
        url.summarize()
        pb = url.content_summarized
        self.assertEqual(pb.is_valid(), True)
