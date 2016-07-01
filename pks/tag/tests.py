#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry

from base.tests import APITestBase, FunctionalTestAfterLoginBase
from content.models import PlaceNote
from place.models import UserPlace


class TagViewTest(APITestBase):
    def test_list(self):
        response = self.client.get('/tags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail(self):
        pass

    def test_create(self):
        pass


class UserPlaceTagViewTest(APITestBase):
    def test_list(self):
        response = self.client.get('/uptags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail(self):
        pass

    def test_create(self):
        pass


class PlaceTagViewTest(APITestBase):
    def test_list(self):
        response = self.client.get('/ptags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail(self):
        pass

    def test_create(self):
        pass


class PostWithTagsTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(PostWithTagsTest, self).setUp()
        self.uplace = UserPlace.objects.create()

    def test_placeNote_with_tags(self):
        json_add = '{"notes": [{"content": "오 여기 #A B #C 인듯~~~"}]}'
        response = self.client.post('/uplaces/', dict(add=json_add, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        want = json_loads(json_add)
        self.assertIsSubsetOf(want, self.uplace.userPost.cjson)
        self.assertIsNotSubsetOf(self.uplace.userPost.cjson, want)
        result_userPost = json_loads(response.content)['userPost']
        self.assertIn(dict(content='A'), result_userPost['tags'])
        self.assertNotIn(dict(content='B'), result_userPost['tags'])
        self.assertIn(dict(content='C'), result_userPost['tags'])

        json_add2 = '{"notes": [{"content": "아 변했음. 여기 이제 A #B #-C 아님"}]}'
        response = self.client.post('/uplaces/', dict(add=json_add2, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.uplace = UserPlace.objects.first()
        self.printJson(self.uplace.userPost.cjson)
        result_userPost = json_loads(response.content)['userPost']
        self.assertIn(dict(content='A'), result_userPost['tags'])
        self.assertIn(dict(content='B'), result_userPost['tags'])
        self.assertNotIn(dict(content='C'), result_userPost['tags'])
