#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import APITestBase
from content import models


class FsVenueViewsetTest(APITestBase):

    def setUp(self):
        '''
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        '''

        self.fs = models.FsVenue(content='40a55d80f964a52020f31ee3')
        self.fs.save()

    def test_list(self):
        response = self.client.get('/fsvs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        fs2 = models.FsVenue(content='40a55d80f964a52020f31ee4')
        fs2.save()
        response = self.client.get('/fsvs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.FsVenue.objects.count())
        response = self.client.post('/fsvs/', dict(content=self.fs.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, models.FsVenue.objects.count())
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.fs.uuid)

        response = self.client.post('/fsvs/', dict(content='40a55d80f964a52020f31ee4'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.FsVenue.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.fs.uuid)


class ShortTextViewsetTest(APITestBase):

    def setUp(self):
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
