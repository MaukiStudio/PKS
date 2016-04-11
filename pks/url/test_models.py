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

    def test_content_summarized(self):
        url = models.Url()
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        url.content = test_data
        url.save()
        post = url.content_summarized
        self.assertEqual(post.is_valid, True)

