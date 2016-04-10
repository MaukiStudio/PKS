#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from django.test import TestCase
from rest_framework import status

from base.tests import APITestBase


class ApiRootTest(APITestBase):

    def setUp(self):
        super(ApiRootTest, self).setUp()
        self.response = self.client.get('/')

    def test_can_connect(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

    def test_valid_json(self):
        json_dict = json.loads(self.response.content)
        self.assertEqual(type(json_dict), dict)


class AdminTest(TestCase):

    def setUp(self):
        super(AdminTest, self).setUp()
        self.response = self.client.get('/admin/')

    def test_can_connect(self):
        self.assertEqual(self.response.status_code, status.HTTP_302_FOUND)
        response2 = self.client.get(self.response.url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
