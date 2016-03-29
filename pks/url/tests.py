#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from rest_framework import status

from base.tests import APITestBase
from url import models


class UrlViewsetTest(APITestBase):

    def setUp(self):
        '''
        response = self.client.post('/users/register/')
        self.auth_user_token = json.loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json.loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        '''

        self.url = models.Url(url='http://www.maukistudio.com/', content='<html>content</html>')
        self.url.save()

    def test_list(self):
        response = self.client.get('/urls/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(list, type(result))
        self.assertEqual(1, len(result))

        url2 = models.Url(url='http://www.maukistudio.com/2')
        url2.save()
        response = self.client.get('/urls/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(list, type(result))
        self.assertEqual(2, len(result))

    def test_create(self):
        self.assertEqual(1, models.Url.objects.count())
        response = self.client.post('/urls/', dict(url=self.url.url, content=self.url.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, models.Url.objects.count())

        response = self.client.post('/urls/', dict(url='http://www.maukistudio.com/2', content='<html>content2</html>'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(2, models.Url.objects.count())
