#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status

from strgen import StringGenerator as SG
from cryptography.fernet import Fernet
from pks.settings import USER_ENC_KEY, VD_ENC_KEY
from account import models
from base.tests import APITestBase


class VDViewSetTest(APITestBase):

    def setUp(self):
        self.response1 = self.client.get(reverse('vd-list'))
        self.response2 = self.client.get(reverse('vd-list'), {'format': 'api'})

    def test_can_connect(self):
        self.assertEqual(self.response1.status_code, status.HTTP_200_OK)
        self.assertEqual(self.response2.status_code, status.HTTP_200_OK)

    def test_valid_json(self):
        decoded = json.JSONDecoder().decode(self.response1.content)
        encoded = json.JSONEncoder(separators=(',', ':')).encode(decoded)
        self.assertEqual(encoded, self.response1.content)


class UserManualRegisterLoginTest(APITestBase):

    def test_register(self):
        response = self.client.post('/users/', {'username': 'gulby', 'password': 'pass'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_connect_by_browser(self):
        response = self.client.get('/api-auth/login/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_internal(self):
        user = User(username='gulby')
        user.set_password('pass')
        user.save()

        user2 = User.objects.first()
        self.assertEqual(user, user2)

        self.assertNotLogin()
        login_result = self.client.login(username='gulby', password='pass')
        self.assertTrue(login_result)
        self.assertLogin(user)

    def test_login_external(self):
        user = User(username='gulby')
        user.set_password('pass')
        user.save()
        self.assertNotLogin()

        response = self.client.post('/api-auth/login/', {'username': 'gulby', 'password': 'pass'})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertLogin(user)

    def test_login_external_fail(self):
        user = User(username='gulby')
        user.set_password('pass')
        user.save()
        response = self.client.post('/api-auth/login/', {'username': 'gulby', 'password': 'fail'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotLogin()


class UserAutoRegisterLoginTest(APITestBase):

    def test_register(self):
        response = self.client.post('/users/register/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = json.loads(response.content)
        self.assertIn('auth_user_token', result)
        decrypter = Fernet(USER_ENC_KEY)
        raw_token = decrypter.decrypt(result['auth_user_token'].encode(encoding='utf-8'))
        pk = int(raw_token.split('|')[0])
        username = raw_token.split('|')[1]
        password = raw_token.split('|')[2]
        user = User.objects.first()
        self.assertEqual(pk, user.pk)
        self.assertEqual(username, user.username)
        self.assertTrue(user.check_password(password))
        self.assertNotLogin()

    def test_login(self):
        response = self.client.post('/users/register/')
        auth_user_token = json.loads(response.content)['auth_user_token']
        user = User.objects.first()
        self.assertNotLogin()

        response = self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertLogin(user)

    def test_login_fail(self):
        response = self.client.post('/users/register/')
        auth_user_token = json.loads(response.content)['auth_user_token']
        user = User.objects.first()
        user.delete()
        response = self.client.post('/users/login/', {'auth_user_token': auth_user_token})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotLogin()


class VDRegisterSetTest(APITestBase):
    def setUp(self):
        response = self.client.post('/users/register/')
        auth_user_token = json.loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': auth_user_token})

    def test_register(self):
        deviceName = SG('[\w\-]{36}').render()
        deviceTypeName = 'LG-F460L'
        email = 'gulby@maukistudio.com'
        response = self.client.post('/vds/register/',
                                    dict(email=email, deviceTypeName=deviceTypeName, deviceName=deviceName))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        saved = models.VD.objects.first()
        user = User.objects.first()
        self.assertEqual(user, saved.owner)
        self.assertEqual(user.email, email)

        result = json.loads(response.content)
        self.assertIn('auth_vd_token', result)
        decrypter = Fernet(VD_ENC_KEY)
        raw_token = decrypter.decrypt(result['auth_vd_token'].encode(encoding='utf-8'))
        pk = int(raw_token.split('|')[0])
        user_pk = int(raw_token.split('|')[1])

        self.assertEqual(pk, saved.pk)
        self.assertEqual(user_pk, user.pk)
