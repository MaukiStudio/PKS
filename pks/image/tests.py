#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import APITestBase
from image import models


class ImageViewsetTest(APITestBase):
    def setUp(self):
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.img = models.Image()
        self.img.file = self.uploadImage('test.jpg')
        self.img.save()

    def test_list(self):
        response = self.client.get('/imgs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), list)
        self.assertEqual(len(result), 1)

    def test_detail(self):
        response = self.client.get('/imgs/%s/' % self.img.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        print(result)
        self.assertIn('uuid', result)
        self.assertEqual(result['uuid'], self.img.uuid)

    def test_create(self):
        with open('image/samples/test.jpg') as f:
            response = self.client.post('/imgs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_twice(self):
        with open('image/samples/test.jpg') as f:
            response = self.client.post('/imgs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        img1 = models.Image.objects.first()
        url1 = img1.file.url

        with open('image/samples/test.jpg') as f:
            response = self.client.post('/imgs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        img2 = models.Image.objects.get(id=img1.id)
        url2 = img2.file.url

        self.assertEqual(url1, url2)
