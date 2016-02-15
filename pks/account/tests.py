#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.test import APITestCase
from rest_framework import status

from account.models import VirtualDevice


class ApiRootTest(APITestCase):
    def test_can_connect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

