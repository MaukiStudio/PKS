#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from django.contrib.auth.models import User
from rest_framework import status

from strgen import StringGenerator as SG
from cryptography.fernet import Fernet
from pks.settings import USER_ENC_KEY
from account import models
from base.tests import APITestBase


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
        user_id = int(raw_token.split('|')[0])
        username = raw_token.split('|')[1]
        password = raw_token.split('|')[2]
        user = User.objects.first()
        self.assertEqual(user_id, user.id)
        self.assertEqual(username, user.username)
        self.assertTrue(user.check_password(password))
        self.assertNotLogin()

    def test_login(self):
        response = self.client.post('/users/register/')
        auth_user_token = json.loads(response.content)['auth_user_token']
        user = User.objects.first()
        self.assertNotLogin()

        response = self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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

    def test_register_with_no_info(self):
        response = self.client.post('/vds/register/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vd = models.VD.objects.first()
        user = User.objects.first()
        self.assertEqual(user, vd.authOwner)

        result = json.loads(response.content)
        self.assertIn('auth_vd_token', result)
        decrypter = Fernet(models.getVdEncKey(user))
        raw_token = decrypter.decrypt(result['auth_vd_token'].encode(encoding='utf-8'))
        vd_id = int(raw_token.split('|')[0])
        user_id = int(raw_token.split('|')[1])

        self.assertEqual(vd_id, vd.id)
        self.assertEqual(user_id, user.id)

    def test_register(self):
        deviceName = SG('[\w\-]{36}').render()
        deviceTypeName = 'LG-F460L'
        email = 'gulby@maukistudio.com'
        country = 'KR'
        language = 'ko'
        timezone = 'KST'
        data = '{"UDID": "blah-blah"}'
        response = self.client.post('/vds/register/',
                                    dict(email=email, deviceTypeName=deviceTypeName, deviceName=deviceName,
                                         country=country, language=language, timezone=timezone, data=data))
        vd = models.VD.objects.first()
        user = User.objects.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(vd.deviceTypeName, deviceTypeName)
        self.assertEqual(vd.deviceName, deviceName)
        self.assertEqual(vd.country, country)
        self.assertEqual(vd.language, language)
        self.assertEqual(vd.timezone, timezone)
        self.assertEqual(vd.data, data)
        self.assertEqual(user, vd.authOwner)
        self.assertEqual(user.email, email)

        result = json.loads(response.content)
        self.assertIn('auth_vd_token', result)
        decrypter = Fernet(models.getVdEncKey(user))
        raw_token = decrypter.decrypt(result['auth_vd_token'].encode(encoding='utf-8'))
        vd_id = int(raw_token.split('|')[0])
        user_id = int(raw_token.split('|')[1])

        self.assertEqual(vd_id, vd.id)
        self.assertEqual(user_id, user.id)

    def test_email_confirm(self):
        # TODO : 향후 이메일 발송 루틴이 구현되면 테스트도 수정해야 한다.
        deviceName = SG('[\w\-]{36}').render()
        deviceTypeName = 'LG-F460L'
        email = 'gulby@maukistudio.com'
        response = self.client.post('/vds/register/',
                                    dict(email=email, deviceTypeName=deviceTypeName, deviceName=deviceName))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # TODO : 이메일 인증 - 발송된 메일을 읽어서, 해당 링크를 호출하는 코드를 추가하고, 하기 테스트코드의 주석을 해제
        vd = models.VD.objects.first()
        #self.assertEqual(vd.realOwner, None)

        #이메일 인증 처리

        # assertion
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
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertVdLogin(self.vd)
        return json.loads(response.content)['auth_vd_token']

    def doLogout(self):
        response = self.client.post('/vds/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertVdNotLogin()

    def test_login_simple(self):
        self.doLogin(self.auth_vd_token)

    def test_logout(self):
        self.doLogin(self.auth_vd_token)
        self.doLogout()

    def test_login_complex(self):
        new_token1 = self.doLogin(self.auth_vd_token)
        self.doLogout()
        self.doLogin(self.auth_vd_token)
        self.doLogout()
        self.doLogin(new_token1)
        self.doLogout()

        # 새로운 token 으로 login 을 하고 나면 기존 token 으로는 login 을 못함
        # TODO : 이 기능은 나중에 구현
        '''
        response = self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertVdNotLogin()
        '''

    def test_login_fail(self):
        self.assertVdNotLogin()
        self.vd.delete()
        response = self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertVdNotLogin()


class VDViewSetTest(APITestBase):

    def setUp(self):
        response = self.client.post('/users/register/')
        auth_user_token = json.loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json.loads(response.content)['auth_vd_token']
        self.vd = models.VD.objects.first()
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})

    def test_vds_list(self):
        response = self.client.get('/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 1)

    def test_vds_detail(self):
        aid = self.vd.aid
        response = self.client.get('/vds/%s/' % aid)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertEqual(result['id'], self.vd.id)


class RealUserViewSetBasicTest(APITestBase):

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

    def test_rus_detail(self):
        response = self.client.get('/rus/%s/' % self.ru.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = json.loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertEqual(result['email'], 'gulby@maukistudio.com')
        self.assertEqual(type(result['vds']), list)

        vds = result['vds']
        self.assertEqual(len(vds), 2)
        self.assertIn(self.vd1.id, vds)
        self.assertIn(self.vd3.id, vds)
        self.assertNotIn(self.vd2.id, vds)
        self.assertNotIn(self.vd4.id, vds)

    def test_rus_myself_without_login(self):
        response = self.client.get('/rus/myself/vds/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RealUserViewsetTest(APITestBase):
    def setUp(self):
        response = self.client.post('/users/register/')
        auth_user_token = json.loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json.loads(response.content)['auth_vd_token']
        self.vd = models.VD.objects.first()
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.ru = models.RealUser.objects.get(email='gulby@maukistudio.com')

    def test_rus_detail(self):
        response = self.client.get('/rus/0/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get('/rus/myself/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_rus_myself_vds(self):
        response = self.client.get('/rus/myself/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vds = json.loads(response.content)
        self.assertEqual(len(vds), 0)   # Login VD 는 포함되지 않음

        self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        response = self.client.get('/rus/myself/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vds = json.loads(response.content)
        self.assertEqual(len(vds), 1)

        self.client.post('/vds/register/', dict(email='hoonja@maukistudio.com'))
        response = self.client.get('/rus/myself/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vds = json.loads(response.content)
        self.assertEqual(len(vds), 1)
