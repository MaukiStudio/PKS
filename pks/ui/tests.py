#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from account.models import User, RealUser, VD
from base.tests import APITestBase
from base.utils import merge_sort

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

    def test_merge_sort(self):
        ll = []
        self.assertEqual(merge_sort(ll, lambda e: e), [])
        ll = [['c', 'b', 'a']]
        self.assertEqual(merge_sort(ll, lambda e: e), ['c', 'b', 'a'])
        ll = ['dba', 'ztd', 'rgb']
        self.assertEqual(merge_sort(ll, lambda e: e), ['z', 't', 'r', 'g', 'd', 'b', 'a'])
        ll = ['yuujdba', 'ztdccccb', 'rgbaaa']
        self.assertEqual(merge_sort(ll, lambda e: e), ['z', 'y', 'u', 't', 'r', 'j', 'g', 'd', 'c', 'b', 'a'])
