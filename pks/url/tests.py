#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from rest_framework import status

from base.tests import APITestBase


class UrlViewsetTest(APITestBase):

    def setUp(self):
        response = self.client.post('/users/register/')
        self.auth_user_token = json.loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json.loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})

    def test_url_list(self):
        response = self.client.get('/urls/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
