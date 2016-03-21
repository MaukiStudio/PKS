#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from django.contrib.auth.models import User
from rest_framework import status

from strgen import StringGenerator as SG
from cryptography.fernet import Fernet
from pks.settings import USER_ENC_KEY, VD_ENC_KEY, VD_SESSION_KEY
from account import models
from base.tests import APITestBase


class VDViewSetTest(APITestBase):

    def setUp(self):
        self.ru = models.RealUser(email='gulby@maukistudio.com')
        self.ru.save()
        self.vd1 = models.VD(deviceName='test vd 1', realOwner=self.ru)
        self.vd2 = models.VD(deviceName='test vd 2')
        self.vd1.save()
        self.vd2.save()

    def test_vds_list(self):
        response = self.client.get('/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(type(result), list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['deviceName'], 'test vd 1')
        self.assertEqual(result[1]['deviceName'], 'test vd 2')

    def test_vds_detail(self):
        response = self.client.get('/vds/%s/' % self.vd1.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertEqual(result['deviceName'], 'test vd 1')
        self.assertEqual(result['realOwner'], self.vd1.realOwner.pk)


class RealUserViewSetTest(APITestBase):

    def setUp(self):
        self.ru = models.RealUser(email='gulby@maukistudio.com')
        self.ru.save()
        self.vd1 = models.VD(deviceName='test vd 1', realOwner=self.ru)
        self.vd2 = models.VD(deviceName='test vd 2')
        self.vd3 = models.VD(deviceName='test vd 3', realOwner=self.ru)
        self.vd1.save()
        self.vd2.save()
        self.vd3.save()
        self.ru_other = models.RealUser(email='hoonja@maukistudio.com')
        self.ru_other.save()
        self.vd4 = models.VD(deviceName='test vd 4', realOwner=self.ru_other)
        self.vd4.save()

    def test_vds_detail(self):
        response = self.client.get('/rus/%s/' % self.ru.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = json.loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertEqual(result['email'], 'gulby@maukistudio.com')
        self.assertEqual(type(result['vds']), list)

        vds = result['vds']
        self.assertEqual(len(vds), 2)
        self.assertIn(self.vd1.pk, vds)
        self.assertIn(self.vd3.pk, vds)
        self.assertNotIn(self.vd2.pk, vds)
        self.assertNotIn(self.vd4.pk, vds)


class UserManualRegisterLoginTest(APITestBase):

    def test_register(self):
        response = self.client.post('/users/', dict(username='gulby', password='pass', email='gulby@maukistudio.com'))
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

        response = self.client.post('/api-auth/login/', dict(username='gulby', password='pass'))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertLogin(user)

    def test_login_external_fail(self):
        user = User(username='gulby')
        user.set_password('pass')
        user.save()
        response = self.client.post('/api-auth/login/', dict(username='gulby', password='fail'))

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


class VDRegisterTest(APITestBase):
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
        vd = models.VD.objects.first()
        user = User.objects.first()
        self.assertEqual(user, vd.authOwner)
        self.assertEqual(user.email, email)

        result = json.loads(response.content)
        self.assertIn('auth_vd_token', result)
        decrypter = Fernet(models.getVdEncKey(user))
        raw_token = decrypter.decrypt(result['auth_vd_token'].encode(encoding='utf-8'))
        pk = int(raw_token.split('|')[0])
        user_pk = int(raw_token.split('|')[1])

        self.assertEqual(pk, vd.pk)
        self.assertEqual(user_pk, user.pk)

    def test_email_confirm(self):
        # TODO : 향후 이메일 발송 루틴이 구현되면 테스트도 수정해야 한다.
        deviceName = SG('[\w\-]{36}').render()
        deviceTypeName = 'LG-F460L'
        email = 'gulby@maukistudio.com'
        response = self.client.post('/vds/register/',
                                    dict(email=email, deviceTypeName=deviceTypeName, deviceName=deviceName))

        # TODO : 이메일 인증 - 발송된 메일을 읽어서, 해당 링크를 호출하는 코드가 추가되어야 함

        # assertion
        vd = models.VD.objects.first()
        self.assertIsNotNone(vd.realOwner)
        self.assertEqual(vd.authOwner.email, vd.realOwner.email)


class VDLoginTest(APITestBase):
    def setUp(self):
        response = self.client.post('/users/register/')
        auth_user_token = json.loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json.loads(response.content)['auth_vd_token']
        self.vd = models.VD.objects.first()

    def doLogin(self, auth_vd_token):
        self.assertVdNotLogin()
        response = self.client.post('/vds/login/', {'auth_vd_token': auth_vd_token})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertVdLogin(self.vd)

    def test_login_simple(self):
        self.doLogin(self.auth_vd_token)

    def test_logout(self):
        self.doLogin(self.auth_vd_token)
        response = self.client.post('/vds/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertVdNotLogin()

    def test_login_fail(self):
        self.assertVdNotLogin()
        self.vd.delete()
        response = self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertVdNotLogin()

