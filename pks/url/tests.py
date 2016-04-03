#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import APITestBase
from url import models


class UrlViewsetTest(APITestBase):

    def setUp(self):
        '''
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        '''

        self.url = models.Url(content='http://www.maukistudio.com/')
        self.url.save()

    def test_list(self):
        response = self.client.get('/urls/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(list, type(result))
        self.assertEqual(1, len(result))

        url2 = models.Url(content='http://www.maukistudio.com/2')
        url2.save()
        response = self.client.get('/urls/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(list, type(result))
        self.assertEqual(2, len(result))

    def test_create(self):
        self.assertEqual(1, models.Url.objects.count())
        response = self.client.post('/urls/', dict(content=self.url.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, models.Url.objects.count())
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.url.uuid)

        response = self.client.post('/urls/', dict(content='http://www.maukistudio.com/2'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(2, models.Url.objects.count())
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.url.uuid)
