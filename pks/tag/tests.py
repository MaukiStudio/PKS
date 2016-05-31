#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import APITestBase


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
