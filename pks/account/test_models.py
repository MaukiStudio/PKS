#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.db import IntegrityError

from strgen import StringGenerator as SG
from account import models


class RealUserTest(TestCase):

    def test_string_representation(self):
        email = 'gulby@maukistudio.com'
        realUser = models.RealUser(email=email)
        self.assertEqual(email, str(realUser))

    def test_save_and_retreive(self):
        realUser = models.RealUser(email='gulby@maukistudio.com')
        realUser.save()
        saved = models.RealUser.objects.first()
        self.assertEqual(saved, realUser)

    def test_email_not_null(self):
        realUser = models.RealUser()
        with self.assertRaises(IntegrityError):
            realUser.save()

    def test_email_property(self):
        email = 'gulby@maukistudio.com'
        realUser = models.RealUser(email=email)
        self.assertEqual(realUser.email, email)
        realUser.save()
        saved = models.RealUser.objects.first()
        self.assertEqual(saved.email, email)

        realUser2 = models.RealUser(email=email)
        with self.assertRaises(IntegrityError):
            realUser2.save()



class VDTest(TestCase):

    def setUp(self):
        self.user = User()
        self.user.username = SG('[\w]{30}').render()
        self.user.password = SG('[\l]{6:10}&[\d]{2}').render()
        self.user.save()

        self.realUser = models.RealUser(email='gulby@maukistudio.com')
        self.realUser.save()

    def test_string_representation(self):
        vd = models.VD(authOwner=self.user, realOwner=self.realUser, deviceTypeName='LG-F460L', deviceName='88:C9:D0:FA:79:57')
        self.assertEqual('gulby@maukistudio.com\'s LG-F460L (88:C9:D0:FA:79:57)', str(vd))

    def test_save_and_retreive(self):
        vd = models.VD()
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved, vd)

    def test_authOwner_property(self):
        vd = models.VD(authOwner=self.user)
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved.authOwner, self.user)

        vd2 = models.VD()
        vd2.authOwner = vd.authOwner
        vd2.save()
        self.assertNotEqual(vd, vd2)
        self.assertEqual(vd.authOwner, vd2.authOwner)

    def test_authOwner_relationship(self):
        self.assertEqual(self.user.vd_set.all().count(), 0)
        vd = models.VD(authOwner=self.user)
        vd.save()
        self.assertEqual(self.user.vd_set.all().count(), 1)
        vd2 = models.VD(authOwner=self.user)
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

    def test_realOwner_property(self):
        vd = models.VD(realOwner=self.realUser)
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved.realOwner, self.realUser)

        vd2 = models.VD()
        vd2.realOwner = vd.realOwner
        vd2.save()
        self.assertNotEqual(vd, vd2)
        self.assertEqual(vd.realOwner, vd2.realOwner)

    def test_realOwner_relationship(self):
        self.assertEqual(self.realUser.vd_set.all().count(), 0)
        vd = models.VD(realOwner=self.realUser)
        vd.save()
        self.assertEqual(self.realUser.vd_set.all().count(), 1)
        vd2 = models.VD(realOwner=self.realUser)
        vd2.save()
        self.assertEqual(self.realUser.vd_set.all().count(), 2)


