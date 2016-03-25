#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from rest_framework import status

from base.tests import APITestBase
from image import models


class ImageViewsetTest(APITestBase):
    def setUp(self):
        response = self.client.post('/users/register/')
        auth_user_token = json.loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json.loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})

    def test_img_list(self):
        response = self.client.get('/imgs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create(self):
        with open('image/test.jpg') as f:
            response = self.client.post('/imgs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_twice(self):
        with open('image/test.jpg') as f:
            response = self.client.post('/imgs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        img1 = models.Image.objects.first()
        url1 = img1.file.url

        with open('image/test.jpg') as f:
            response = self.client.post('/imgs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        img2 = models.Image.objects.get(pk=img1.pk)
        url2 = img2.file.url

        self.assertEqual(url1, url2)
