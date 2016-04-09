#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads, dumps as json_dumps
from account.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.db import IntegrityError

from base.tests import APITestBase
from strgen import StringGenerator as SG
from cryptography.fernet import InvalidToken
from account import models


class RealUserTest(APITestBase):

    def test_string_representation(self):
        email = 'gulby@maukistudio.com'
        realUser = models.RealUser(email=email)
        self.assertEqual(email, unicode(realUser))

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


class VDTest(APITestBase):

    def setUp(self):
        self.user = User()
        self.user.username = SG('[\w]{30}').render()
        self.user.password = SG('[\l]{6:10}&[\d]{2}').render()
        self.user.save()

        self.realUser = models.RealUser(email='gulby@maukistudio.com')
        self.realUser.save()

    def test_string_representation(self):
        vd1 = models.VD()
        self.assertEqual("unknown@email's unknown device", unicode(vd1))
        vd2 = models.VD(authOwner=self.user, realOwner=self.realUser, deviceTypeName='LG-F460L', deviceName='88:C9:D0:FA:79:57')
        self.assertEqual("gulby@maukistudio.com's LG-F460L (88:C9:D0:FA:79:57)", unicode(vd2))

    def test_save_and_retreive(self):
        vd = models.VD()
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved, vd)

    def test_simple_properties(self):
        deviceName = SG('[\w\-]{36}').render()
        deviceTypeName = 'LG-F460L'
        country = 'KR'
        language = 'ko'
        timezone = 'KST'
        vd = models.VD()
        vd.deviceName = deviceName
        vd.deviceTypeName = deviceTypeName
        vd.country = country
        vd.language = language
        vd.timezone = timezone
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(saved.deviceName, deviceName)
        self.assertEqual(saved.deviceTypeName, deviceTypeName)
        self.assertEqual(saved.country, country)
        self.assertEqual(saved.language, language)
        self.assertEqual(saved.timezone, timezone)

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
        self.assertEqual(self.user.vds.all().count(), 0)
        vd = models.VD(authOwner=self.user)
        vd.save()
        self.assertEqual(self.user.vds.all().count(), 1)
        vd2 = models.VD(authOwner=self.user)
        vd2.save()
        self.assertEqual(self.user.vds.all().count(), 2)

    def test_data_property(self):
        j = '{"deviceName": "%s", "deviceTypeName": "%s"}' % (SG('[\w\-]{36}').render(), 'LG-F460L')
        vd = models.VD()
        vd.data = json_loads(j)
        vd.save()
        saved = models.VD.objects.first()
        self.assertEqual(j, json_dumps(saved.data, encoding='utf-8'))

    def test_lastLonLat_property(self):
        point = GEOSGeometry('POINT(127.1037430 37.3997320)')
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
        self.assertEqual(self.realUser.vds.all().count(), 0)
        vd = models.VD(realOwner=self.realUser)
        vd.save()
        self.assertEqual(self.realUser.vds.all().count(), 1)
        vd2 = models.VD(realOwner=self.realUser)
        vd2.save()
        self.assertEqual(self.realUser.vds.all().count(), 2)

    def test_aid(self):
        vd1 = models.VD(authOwner=self.user)
        vd1.save()
        vd1_aid = unicode(vd1.aid)
        user2 = User(username='another')
        user2.save()
        vd1.authOwner = user2
        vd1_aid2 = unicode(vd1.aid)

        self.assertGreater(len(vd1_aid), 32)
        self.assertNotEqual(vd1_aid, unicode(vd1.id))
        self.assertNotEqual(vd1_aid2, unicode(vd1.id))
        self.assertEqual(vd1.aid2id(vd1_aid2), vd1.id)
        with self.assertRaises(InvalidToken):
            vd1.aid2id(vd1_aid)
