#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry

from strgen import StringGenerator as SG
from account import models


class VDTest(TestCase):

    def setUp(self):
        self.user = User()
        self.user.username = SG('[\w]{30}').render()
        self.user.password = SG('[\l]{6:10}&[\d]{2}').render()
        self.user.save()

        self.vd = models.VD()
        self.vd.user = self.user

    def test_save_and_retreive(self):
        self.vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved, self.vd)
        self.assertEqual(saved.user, self.user)

    def test_can_save_same_user(self):
        self.vd.save()
        vd2 = models.VD()
        vd2.user = self.vd.user
        vd2.save()
        self.assertNotEqual(self.vd, vd2)
        self.assertEqual(self.vd.user, vd2.user)

    def test_simple_properties(self):
        deviceName = SG('[\w\-]{36}').render()
        deviceTypeName = 'LG-F460L'
        self.vd.deviceName = deviceName
        self.vd.deviceTypeName = deviceTypeName
        self.vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved.deviceName, deviceName)
        self.assertEqual(saved.deviceTypeName, deviceTypeName)

    def test_json_properties(self):
        j = '{"deviceName": "%s", "deviceTypeName": "%s"}' % (SG('[\w\-]{36}').render(), 'LG-F460L')
        self.vd.data = json.loads(j)
        self.vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(j, json.dumps(saved.data, encoding='utf-8'))

    def test_gis_properties(self):
        point = GEOSGeometry('POINT(127.0850802 37.4005048)')
        self.vd.last_lonlat = point
        self.vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(point, saved.last_lonlat)