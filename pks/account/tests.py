#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry

from strgen import StringGenerator as SG
from cryptography.fernet import Fernet
from pks.settings import USER_ENC_KEY
from account.models import User, RealUser, VD, Storage, Tracking
from base.tests import APITestBase, FunctionalTestAfterLoginBase


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
        result = json_loads(response.content)
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
        auth_user_token = json_loads(response.content)['auth_user_token']
        user = User.objects.first()
        self.assertNotLogin()

        response = self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLogin(user)

    def test_login_fail(self):
        response = self.client.post('/users/register/')
        auth_user_token = json_loads(response.content)['auth_user_token']
        user = User.objects.first()
        user.delete()
        response = self.client.post('/users/login/', {'auth_user_token': auth_user_token})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotLogin()


class VDRegisterTest(APITestBase):
    def setUp(self):
        super(VDRegisterTest, self).setUp()
        response = self.client.post('/users/register/')
        auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': auth_user_token})

    def test_register_with_no_info(self):
        response = self.client.post('/vds/register/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vd = VD.objects.first()
        user = User.objects.first()
        self.assertEqual(user, vd.authOwner)

        result = json_loads(response.content)
        self.assertIn('auth_vd_token', result)
        decrypter = Fernet(user.crypto_key)
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
        self.assertEqual(VD.objects.count(), 0)
        response = self.client.post('/vds/register/',
                                    dict(email=email, deviceTypeName=deviceTypeName, deviceName=deviceName,
                                         country=country, language=language, timezone=timezone, data=data))
        self.assertEqual(VD.objects.count(), 1)
        vd = VD.objects.first()
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

        result = json_loads(response.content)
        self.assertIn('auth_vd_token', result)
        decrypter = Fernet(user.crypto_key)
        raw_token = decrypter.decrypt(result['auth_vd_token'].encode(encoding='utf-8'))
        vd_id = int(raw_token.split('|')[0])
        user_id = int(raw_token.split('|')[1])

        self.assertEqual(vd_id, vd.id)
        self.assertEqual(user_id, user.id)
        self.assertEqual(vd.realOwner, None)

    def test_register_by_facebook(self):
        email = '1234567890@facebook'
        self.assertEqual(VD.objects.count(), 0)
        response = self.client.post('/vds/register/', dict(email=email))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vd = VD.objects.first()
        self.assertNotEqual(vd.realOwner, None)

    def test_register_by_kakaotalk(self):
        email = '1234567890@kakaotalk'
        self.assertEqual(VD.objects.count(), 0)
        response = self.client.post('/vds/register/', dict(email=email))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vd = VD.objects.first()
        self.assertNotEqual(vd.realOwner, None)

    def test_email_confirm(self):
        # TODO : 향후 이메일 발송 루틴이 구현되면 테스트도 수정해야 한다.
        deviceName = SG('[\w\-]{36}').render()
        deviceTypeName = 'LG-F460L'
        email = 'gulby@maukistudio.com'
        response = self.client.post('/vds/register/',
                                    dict(email=email, deviceTypeName=deviceTypeName, deviceName=deviceName))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        vd = VD.objects.first()
        self.assertEqual(vd.realOwner, None)

        # 이메일 인증 처리
        token = vd.getEmailConfirmToken(email)
        response = self.client.get('/vds/confirm/', dict(email_confirm_token=token))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/ui/confirm_ok/')

        # assertion
        vd = VD.objects.first()
        self.assertIsNotNone(vd.realOwner)
        self.assertEqual(vd.authOwner.email, vd.realOwner.email)

        # 또 이메일 인증 처리 : 링크는 여러번 누를 수도...
        self.assertEqual(VD.objects.count(), 1)
        self.assertEqual(RealUser.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        token = vd.getEmailConfirmToken(email)
        response = self.client.get('/vds/confirm/', dict(email_confirm_token=token))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(VD.objects.count(), 1)
        self.assertEqual(RealUser.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)


class VDLoginTest(APITestBase):
    def setUp(self):
        super(VDLoginTest, self).setUp()
        response = self.client.post('/users/register/')
        auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.vd = VD.objects.first()

    def doLogin(self, auth_vd_token):
        self.assertVdNotLogin()
        response = self.client.post('/vds/login/', {'auth_vd_token': auth_vd_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertVdLogin(self.vd)
        return json_loads(response.content)['auth_vd_token']

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


class VDViewSetTest(FunctionalTestAfterLoginBase):

    def test_vds_list(self):
        response = self.client.get('/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 1)

    def test_vds_detail(self):
        aid = self.vd.aid
        response = self.client.get('/vds/%s/' % aid)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertEqual(result['id'], self.vd.id)


class RealUserViewSetBasicTest(APITestBase):

    def setUp(self):
        super(RealUserViewSetBasicTest, self).setUp()
        self.ru = RealUser(email='gulby@maukistudio.com')
        self.ru.save()
        self.vd1 = VD(deviceName='test vd 1', realOwner=self.ru)
        self.vd2 = VD(deviceName='test vd 2')
        self.vd3 = VD(deviceName='test vd 3', realOwner=self.ru)
        self.vd1.save()
        self.vd2.save()
        self.vd3.save()
        self.ru_other = RealUser(email='hoonja@maukistudio.com')
        self.ru_other.save()
        self.vd4 = VD(deviceName='test vd 4', realOwner=self.ru_other)
        self.vd4.save()

    def test_rus_detail(self):
        response = self.client.get('/rus/%s/' % self.ru.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = json_loads(response.content)
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


class RealUserViewsetTest(FunctionalTestAfterLoginBase):
    def setUp(self):
        super(RealUserViewsetTest, self).setUp()
        email = self.input_from_user()
        self.ru = RealUser.objects.get(email=email)

    def test_rus_detail(self):
        response = self.client.get('/rus/0/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get('/rus/myself/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vd.realOwner = None
        self.vd.save()
        response = self.client.get('/rus/myself/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rus_myself_vds(self):
        response = self.client.get('/rus/myself/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vds = json_loads(response.content)
        self.assertEqual(len(vds), 0)   # Login VD 는 포함되지 않음

        '''
        self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        response = self.client.get('/rus/myself/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vds = json_loads(response.content)
        self.assertEqual(len(vds), 1)

        self.client.post('/vds/register/', dict(email='hoonja@maukistudio.com'))
        response = self.client.get('/rus/myself/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vds = json_loads(response.content)
        self.assertEqual(len(vds), 1)
        #'''

    def test_rus_patch(self):
        other_ru = RealUser.objects.create(email='test@test.com', nickname='other_ru')
        response = self.client.get('/rus/myself/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ru = RealUser.objects.get(id=self.ru.id)
        self.assertEqual(ru.nickname, None)
        response = self.client.patch('/rus/myself/', dict(nickname='gulby'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ru = RealUser.objects.get(id=self.ru.id)
        self.assertEqual(ru.nickname, 'gulby')
        response = self.client.patch('/rus/myself/', dict(nickname='other_ru'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StorageViewsetTest(FunctionalTestAfterLoginBase):
    def setUp(self):
        super(StorageViewsetTest, self).setUp()
        self.vd = VD.objects.get(id=self.vd_id)
        self.storage = Storage()
        self.storage.vd = self.vd
        self.storage.key = 'test_key'
        self.storage.value = {'test_sub_key': 'test_value'}
        self.storage.save()

    def test_storages_detail(self):
        response = self.client.get('/storages/test_key/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get('/storages/new_key/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TrackingViewSetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(TrackingViewSetTest, self).setUp()
        lonLat = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        self.tracking = Tracking.create(self.vd_id, lonLat)

    def test_list(self):
        response = self.client.get('/trackings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        self.assertIn('vd_id', results[0])
        self.assertIn('created', results[0])

    def test_create(self):
        self.assertEqual(Tracking.objects.count(), 1)
        json = '{"lat": 37.3997320, "lon": 127.1037430}'
        response = self.client.post('/trackings/', dict(value=json))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tracking.objects.count(), 2)
