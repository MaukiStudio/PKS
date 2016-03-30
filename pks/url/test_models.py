#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.utils import timezone
from datetime import timedelta
from uuid import uuid1
from django.db import IntegrityError

from base.tests import APITestBase
from url import models


class UrlTest(APITestBase):

    def test_string_representation(self):
        url = models.Url()
        url.url = 'http://www.maukistudio.com/'
        self.assertEqual(unicode(url), url.url)

    def test_save_and_retreive(self):
        url = models.Url()
        url.uuid = uuid1()
        url.save()
        saved = models.Url.objects.first()
        self.assertEqual(saved, url)
        self.assertEqual(saved.uuid, url.uuid)

    def test_url_property(self):
        url = models.Url()
        test_value = 'http://www.maukistudio.com/'
        url.url = test_value
        url.save()
        saved = models.Url.objects.first()
        self.assertEqual(saved.url, test_value)

        url2 = models.Url()
        url2.url = url.url
        self.assertEqual(1, models.Url.objects.count())
        url.save()
        self.assertEqual(1, models.Url.objects.count())

        with self.assertRaises(IntegrityError):
            models.Url.objects.create(url=url.url)

    def test_content_property(self):
        url = models.Url(url='http://www.maukistudio.com/')
        test_value = '<html>maukistudio</html>'
        url.content = test_value
        url.save()
        saved = models.Url.objects.first()
        self.assertEqual(saved.content, test_value)

    def test_lastAccessDate_property(self):
        url = models.Url(url='http://www.maukistudio.com/')
        url.save()
        saved = models.Url.objects.first()
        self.assertEqual(None, url.lastCrawlDate)
        self.assertEqual(None, saved.lastCrawlDate)

        url.content = 'content'
        url.save()
        self.assertAlmostEqual(timezone.now(), url.lastCrawlDate, delta=timedelta(seconds=1))
        saved = models.Url.objects.first()
        self.assertEqual(saved.lastCrawlDate, url.lastCrawlDate)
