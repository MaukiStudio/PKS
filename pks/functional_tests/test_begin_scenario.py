#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import FunctionalTestBase


class RegisterScenarioTest(FunctionalTestBase):

    def test_register(self):
        # Register User (only for auth)
        response = self.client.post('/users/register/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.secureStorage['auth_user_token'] = json_loads(response.content)['auth_user_token']

        # User Login by Token
        self.assertNotLogin()
        response = self.client.post('/users/login/', dict(auth_user_token=self.secureStorage['auth_user_token']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLogin()

        # Register VD
        email = self.input_from_user()
        country = 'KR'
        language = 'ko'
        timezone = 'KST'
        data = '{"any json": "ok"}'
        response = self.client.post('/vds/register/', dict(email=email, country=country, language=language, timezone=timezone, data=data))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']


class LoginScenarioTest(FunctionalTestBase):

    def setUp(self):
        super(LoginScenarioTest, self).setUp()
        response = self.client.post('/users/register/')
        self.secureStorage['auth_user_token'] = json_loads(response.content)['auth_user_token']
        response = self.client.post('/users/login/', dict(auth_user_token=self.secureStorage['auth_user_token']))
        email = self.input_from_user()
        response = self.client.post('/vds/register/', dict(email=email,))
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']
        self.logout()

    def test_login(self):

        # User 로그인 by Token
        self.assertNotLogin()
        response = self.client.post('/users/login/', dict(auth_user_token=self.secureStorage['auth_user_token']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLogin()

        # VD 로그인
        self.assertVdNotLogin()
        response = self.client.post('/vds/login/', dict(auth_vd_token=self.normalStorage['auth_vd_token']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertVdLogin()
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']
