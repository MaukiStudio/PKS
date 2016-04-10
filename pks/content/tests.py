#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import APITestBase
from content import models


class LegacyPlaceViewsetTest(APITestBase):

    def setUp(self):
        super(LegacyPlaceViewsetTest, self).setUp()
        '''
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        '''

        self.lp = models.LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square')
        self.lp.save()

    def test_list(self):
        response = self.client.get('/lps/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        lp2 = models.LegacyPlace(content='http://map.naver.com/local/siteview.nhn?code=21149144')
        lp2.save()
        response = self.client.get('/lps/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.LegacyPlace.objects.count())
        response = self.client.post('/lps/', dict(content=self.lp.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, models.LegacyPlace.objects.count())
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.lp.uuid)

        response = self.client.post('/lps/', dict(content='http://map.naver.com/local/siteview.nhn?code=21149144'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.LegacyPlace.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.lp.uuid)


class ShortTextViewsetTest(APITestBase):

    def setUp(self):
        super(ShortTextViewsetTest, self).setUp()
        self.stxt = models.ShortText(content='경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)')
        self.stxt.save()

    def test_list(self):
        response = self.client.get('/stxts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        stxt2 = models.ShortText(content='경기도 하남시 풍산로 270 미사강변도시2단지 206동 402호')
        stxt2.save()
        response = self.client.get('/stxts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.ShortText.objects.count())
        response = self.client.post('/stxts/', dict(content=self.stxt.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.ShortText.objects.count(), 1)
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.stxt.uuid)

        response = self.client.post('/stxts/', dict(content='경기도 하남시 풍산로 270 미사강변도시2단지 206동 402호'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.ShortText.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.stxt.uuid)


class PhoneNumberViewsetTest(APITestBase):

    def setUp(self):
        super(PhoneNumberViewsetTest, self).setUp()
        self.phone = models.PhoneNumber(content='010-5475-9245')
        self.phone.save()

    def test_list(self):
        response = self.client.get('/phones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        phone2 = models.PhoneNumber(content='010-5686-1613')
        phone2.save()
        response = self.client.get('/phones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.PhoneNumber.objects.count())
        response = self.client.post('/phones/', dict(content=self.phone.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.PhoneNumber.objects.count(), 1)
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.phone.uuid)

        response = self.client.post('/phones/', dict(content='010-5686-1613'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.PhoneNumber.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.phone.uuid)
