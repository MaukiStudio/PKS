#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.test import APITestCase
from rest_framework import status


class ApiRootTest(APITestCase):

    def setUp(self):
        self.response = self.client.get('/')

    def test_can_connect(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)
