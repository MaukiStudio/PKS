#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import APITestBase
from image import models
from account.models import VD


class ImageViewsetTest(APITestBase):
    def setUp(self):
        super(ImageViewsetTest, self).setUp()
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.img = models.Image()
        self.img.content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        self.img.save()
        self.content2 = 'http://blogpfthumb.phinf.naver.net/20100110_16/mardukas_1263055491560_VI01Ic_JPG/DSCN1968.JPG'

    def test_list(self):
        response = self.client.get('/imgs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

    def test_detail(self):
        response = self.client.get('/imgs/%s/' % self.img.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertNotIn('dhash', result)
        self.assertEqual(result['uuid'], self.img.uuid)

    def test_create(self):
        response = self.client.post('/imgs/', dict(content=self.content2))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_twice(self):
        self.assertEqual(models.Image.objects.count(), 1)
        response = self.client.post('/imgs/', dict(content=self.content2))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.Image.objects.count(), 2)

        response = self.client.post('/imgs/', dict(content=self.content2))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.Image.objects.count(), 2)


class RawFileViewsetTest(APITestBase):
    def setUp(self):
        super(RawFileViewsetTest, self).setUp()
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.vd = VD.objects.first()
        self.rf = models.RawFile()
        self.rf.file = self.uploadFile('test.png')
        self.rf.vd = self.vd
        self.rf.save()

    def test_list(self):
        response = self.client.get('/rfs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

    def test_detail(self):
        response = self.client.get('/rfs/%s/' % self.rf.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertIn('uuid', result)
        self.assertIn('vd', result)
        self.assertIn('file', result)
        self.assertNotIn('id', result)
        self.assertNotIn('dhash', result)
        self.assertEqual(result['uuid'], self.rf.uuid)
        self.assertEqual(result['vd'], self.vd.id)

    def test_create(self):
        self.assertEqual(models.RawFile.objects.count(), 1)
        self.assertVdLogin()
        self.assertNotEqual(self.vd_id, None)
        with open('image/samples/test.png') as f:
            response = self.client.post('/rfs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.RawFile.objects.count(), 2)
        result = json_loads(response.content)
        self.assertEqual(result['vd'], self.vd.id)
