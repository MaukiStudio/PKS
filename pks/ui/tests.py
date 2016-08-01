#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from account.models import User, RealUser, VD
from base.tests import APITestBase


class ListTest(APITestBase):

    def test_diaries_connect(self):
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(VD.objects.count(), 0)
        self.assertEqual(RealUser.objects.count(), 0)
        self.assertNotLogin()
        self.assertVdNotLogin()
        response = self.client.get('/ui/diaries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(VD.objects.count(), 1)
        self.assertEqual(RealUser.objects.count(), 0)
        self.assertNotLogin()
        self.assertVdLogin()
