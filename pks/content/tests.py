#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from rest_framework import status

from base.tests import APITestBase
from content import models


class FsVenueViewsetTest(APITestBase):

    def setUp(self):
        '''
        response = self.client.post('/users/register/')
        self.auth_user_token = json.loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json.loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        '''

        self.fs = models.FsVenue(content='40a55d80f964a52020f31ee3')
        self.fs.save()

    def test_list(self):
        response = self.client.get('/fsvs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(list, type(result))
        self.assertEqual(1, len(result))

        fs2 = models.FsVenue(content='40a55d80f964a52020f31ee4')
        fs2.save()
        response = self.client.get('/fsvs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(list, type(result))
        self.assertEqual(2, len(result))

    def test_create(self):
        self.assertEqual(1, models.FsVenue.objects.count())
        response = self.client.post('/fsvs/', dict(content=self.fs.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, models.FsVenue.objects.count())

        response = self.client.post('/fsvs/', dict(content='40a55d80f964a52020f31ee4'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(2, models.FsVenue.objects.count())


class ShortTextViewsetTest(APITestBase):

    def setUp(self):
        self.stxt = models.ShortText(content='경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)')
        self.stxt.save()

    def test_list(self):
        response = self.client.get('/stxts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(list, type(result))
        self.assertEqual(1, len(result))

        stxt2 = models.ShortText(content='경기도 하남시 풍산로 270 미사강변도시2단지 206동 402호')
        stxt2.save()
        response = self.client.get('/stxts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(list, type(result))
        self.assertEqual(2, len(result))

    def test_create(self):
        self.assertEqual(1, models.ShortText.objects.count())
        response = self.client.post('/stxts/', dict(content=self.stxt.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, models.ShortText.objects.count())

        response = self.client.post('/stxts/', dict(content='경기도 하남시 풍산로 270 미사강변도시2단지 206동 402호'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(2, models.ShortText.objects.count())
