#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase
from rest_framework import status


class VirtualDeviceTest(APITestCase):

    def setUp(self):
        self.response1 = self.client.get(reverse('virtualdevice-list'))
        self.response2 = self.client.get(reverse('virtualdevice-list'), {'format': 'api'})

    def test_can_connect(self):
        self.assertEqual(self.response1.status_code, status.HTTP_200_OK)
        self.assertEqual(self.response2.status_code, status.HTTP_200_OK)

    def test_valid_json(self):
        decoded = json.JSONDecoder().decode(self.response1.content)
        encoded = json.JSONEncoder(separators=(',', ':')).encode(decoded)
        self.assertEqual(encoded, self.response1.content)
