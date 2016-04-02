#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.utils import timezone
from datetime import timedelta
from uuid import uuid1
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
        test_id = uuid1()
        url.id = test_id
        url.save()
        saved = models.Url.objects.first()
        self.assertEqual(url.id, test_id)
        self.assertEqual(url.uuid, '%s.url' % b16encode(test_id.bytes))
        self.assertEqual(saved, url)
        self.assertEqual(saved.id, test_id)
        saved2 = models.Url.get_from_uuid(url.uuid)
        self.assertEqual(saved2, url)

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
