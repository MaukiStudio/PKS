#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry

from base.tests import APITestBase
from place import models
from image.models import Image
from content.models import ShortText
from url.models import Url


class PlaceViewSetTest(APITestBase):

    def setUp(self):
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.place = models.Place(); self.place.save()

    def test_list(self):
        response = self.client.get('/places/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), list)
        self.assertEqual(len(result), 1)

    def test_detail(self):
        response = self.client.get('/places/%s/' % self.place.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        response = self.client.get('/places/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_post(self):
        point1 = GEOSGeometry('POINT(127 37)')
        name1 = ShortText(content='능라'); name1.save()
        addr1 = ShortText(content='경기도 성남시 분당구 운중동 883-3'); addr1.save()
        note11 = ShortText(content='분당 냉면 최고'); note11.save()
        note12 = ShortText(content='만두도 괜찮음'); note12.save()
        imgNote1 = ShortText(content='냉면 사진'); imgNote1.save()
        img1 = Image(file=self.uploadImage('test.jpg')); img1.save()
        img2 = Image(file=self.uploadImage('no_exif_test.jpg')); img2.save()
        url1 = Url(content='http://maukistudio.com/'); url1.save()

        json_str = '''
            {
                "id": %d,
                "lonLat": {"lon": %f, "lat": %f},
                "name": "%s",
                "addr": "%s",
                "notes": ["%s", "%s"],
                "images": [{"uuid": "%s", "note": "%s"}, {"uuid": "%s", "note": null}],
                "urls": ["%s"],
                "fsVenue": null
            }
        ''' % (self.place.id, point1.x, point1.y, name1.uuid, addr1.uuid, note12.uuid, note11.uuid,
               img1.uuid, imgNote1.uuid, img2.uuid, url1.uuid)

        response = self.client.put('/places/post', dict(myPost=json_str))
        print(json_str)
        print(json_loads(json_str))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(self.place.getPost(None), json_loads(json_str))


class PlaceContentViewSetTest(APITestBase):

    def setUp(self):
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})

    def test_list_no_place(self):
        response = self.client.get('/pcs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), list)
        self.assertEqual(len(result), 0)

