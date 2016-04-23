#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from django.test import TestCase
from rest_framework import status
from django.conf import settings

from pks.tasks import for_unit_test
from pks.celery import app


class ApiRootTest(TestCase):

    def setUp(self):
        super(ApiRootTest, self).setUp()
        self.response = self.client.get('/')

    def test_can_connect(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

    def test_valid_json(self):
        json_dict = json_loads(self.response.content)
        self.assertEqual(type(json_dict), dict)


class AdminTest(TestCase):

    def setUp(self):
        super(AdminTest, self).setUp()
        self.response = self.client.get('/admin/')

    def test_can_connect(self):
        self.assertEqual(self.response.status_code, status.HTTP_302_FOUND)
        response2 = self.client.get(self.response.url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)


class CeleryAsyncTest(TestCase):

    def setUp(self):
        settings.CELERY_ALWAYS_EAGER = False
        app.conf.CELERY_ALWAYS_EAGER = False

    def test_basic(self):
        r = for_unit_test.delay('test ', 'async')
        self.assertEqual(r.state, 'PENDING')
        self.assertEqual(r.get(timeout=1), 'test async')


class CelerySyncTest(TestCase):

    def setUp(self):
        settings.CELERY_ALWAYS_EAGER = True
        app.conf.CELERY_ALWAYS_EAGER = True

    def test_unittest(self):
        r = for_unit_test.delay('test ', 'sync')
        self.assertEqual(r.state, 'SUCCESS')
        self.assertEqual(r.result, 'test sync')
