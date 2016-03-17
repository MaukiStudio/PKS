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

    def test_save_and_retreive(self):
        vd = models.VD()
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved, vd)

    def test_owner_property(self):
        vd = models.VD(owner=self.user)
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved.owner, self.user)

        vd2 = models.VD()
        vd2.owner = vd.owner
        vd2.save()
        self.assertNotEqual(vd, vd2)
        self.assertEqual(vd.owner, vd2.owner)

    def test_owner_relationship(self):
        self.assertEqual(self.user.vd_set.all().count(), 0)
        vd = models.VD(owner=self.user)
        vd.save()
        self.assertEqual(self.user.vd_set.all().count(), 1)
        vd2 = models.VD(owner=self.user)
        vd2.save()
        self.assertEqual(self.user.vd_set.all().count(), 2)

    def test_simple_properties(self):
        deviceName = SG('[\w\-]{36}').render()
        deviceTypeName = 'LG-F460L'
        vd = models.VD()
        vd.deviceName = deviceName
        vd.deviceTypeName = deviceTypeName
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved.deviceName, deviceName)
        self.assertEqual(saved.deviceTypeName, deviceTypeName)

    def test_data_property(self):
        j = '{"deviceName": "%s", "deviceTypeName": "%s"}' % (SG('[\w\-]{36}').render(), 'LG-F460L')
        vd = models.VD()
        vd.data = json.loads(j)
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(j, json.dumps(saved.data, encoding='utf-8'))

    def test_lastLonLat_property(self):
        point = GEOSGeometry('POINT(127.0850802 37.4005048)')
        vd = models.VD()
        vd.lastLonLat = point
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(point, saved.lastLonLat)


class RealUserTest(TestCase):

    def test_save_and_retreive(self):
        real_user = models.RealUser()
        real_user.save()
        saved = models.RealUser.objects.first()
        self.assertEqual(saved, real_user)

