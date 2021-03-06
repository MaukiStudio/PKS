#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads, dumps as json_dumps
from django.contrib.gis.geos import GEOSGeometry
from django.db import IntegrityError

from base.tests import APITestBase, FunctionalTestAfterLoginBase
from strgen import StringGenerator as SG
from cryptography.fernet import InvalidToken
from account.models import User, RealUser, VD, Storage, Tracking
from base.utils import get_timestamp, send_email
from pks.settings import WORK_ENVIRONMENT


class RealUserTest(APITestBase):

    def test_string_representation(self):
        email = 'gulby@maukistudio.com'
        realUser = RealUser(email=email)
        self.assertEqual(email, unicode(realUser))

    def test_save_and_retreive(self):
        realUser = RealUser(email='gulby@maukistudio.com')
        realUser.save()
        saved = RealUser.objects.first()
        self.assertEqual(saved, realUser)

    def test_email_not_null(self):
        realUser = RealUser()
        with self.assertRaises(ValueError):
            realUser.save()

    def test_email_property(self):
        email = 'gulby@maukistudio.com'
        realUser = RealUser(email=email)
        self.assertEqual(realUser.email, email)
        realUser.save()
        saved = RealUser.objects.first()
        self.assertEqual(saved.email, email)

        realUser2 = RealUser(email=email)
        with self.assertRaises(IntegrityError):
            realUser2.save()


class VDTest(APITestBase):

    def setUp(self):
        super(VDTest, self).setUp()
        self.user = User()
        self.user.username = SG('[\w]{30}').render()
        self.user.password = SG('[\l]{6:10}&[\d]{2}').render()
        self.user.save()

        self.realUser = RealUser(email='gulby@maukistudio.com')
        self.realUser.save()

    def test_string_representation(self):
        vd1 = VD()
        self.assertEqual("unknown@email's unknown device", unicode(vd1))
        vd2 = VD(authOwner=self.user, realOwner=self.realUser, deviceTypeName='LG-F460L', deviceName='88:C9:D0:FA:79:57')
        self.assertEqual("gulby@maukistudio.com's LG-F460L (88:C9:D0:FA:79:57)", unicode(vd2))

    def test_save_and_retreive(self):
        vd = VD()
        vd.save()
        saved = VD.objects.first()
        self.assertEqual(saved, vd)

    def test_simple_properties(self):
        deviceName = SG('[\w\-]{36}').render()
        deviceTypeName = 'LG-F460L'
        country = 'KR'
        language = 'ko'
        timezone = 'KST'
        vd = VD()
        vd.deviceName = deviceName
        vd.deviceTypeName = deviceTypeName
        vd.country = country
        vd.language = language
        vd.timezone = timezone
        vd.save()
        saved = VD.objects.first()
        self.assertEqual(saved.deviceName, deviceName)
        self.assertEqual(saved.deviceTypeName, deviceTypeName)
        self.assertEqual(saved.country, country)
        self.assertEqual(saved.language, language)
        self.assertEqual(saved.timezone, timezone)

    def test_authOwner_property(self):
        vd = VD(authOwner=self.user)
        vd.save()
        saved = VD.objects.first()
        self.assertEqual(saved.authOwner, self.user)

        vd2 = VD()
        vd2.authOwner = vd.authOwner
        vd2.save()
        self.assertNotEqual(vd, vd2)
        self.assertEqual(vd.authOwner, vd2.authOwner)

    def test_authOwner_relationship(self):
        self.assertEqual(self.user.vds.all().count(), 0)
        vd = VD(authOwner=self.user)
        vd.save()
        self.assertEqual(self.user.vds.all().count(), 1)
        vd2 = VD(authOwner=self.user)
        vd2.save()
        self.assertEqual(self.user.vds.all().count(), 2)

    def test_data_property(self):
        j = '{"deviceName": "%s", "deviceTypeName": "%s"}' % (SG('[\w\-]{36}').render(), 'LG-F460L')
        vd = VD()
        vd.data = json_loads(j)
        vd.save()
        saved = VD.objects.first()
        self.assertEqual(j, json_dumps(saved.data, encoding='utf-8'))

    def test_lastLonLat_property(self):
        point = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        vd = VD()
        vd.lastLonLat = point
        vd.save()
        saved = VD.objects.first()
        self.assertEqual(point, saved.lastLonLat)

    def test_realOwner_property(self):
        vd = VD(realOwner=self.realUser)
        vd.save()
        saved = VD.objects.first()
        self.assertEqual(saved.realOwner, self.realUser)

        vd2 = VD()
        vd2.realOwner = vd.realOwner
        vd2.save()
        self.assertNotEqual(vd, vd2)
        self.assertEqual(vd.realOwner, vd2.realOwner)

    def test_realOwner_relationship(self):
        self.assertEqual(self.realUser.vds.all().count(), 0)
        vd = VD(realOwner=self.realUser)
        vd.save()
        self.assertEqual(self.realUser.vds.all().count(), 1)
        vd2 = VD(realOwner=self.realUser)
        vd2.save()
        self.assertEqual(self.realUser.vds.all().count(), 2)

    def test_aid(self):
        vd1 = VD(authOwner=self.user)
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

    def test_parent(self):
        vd_parent = VD()
        vd_parent.save()
        self.assertEqual(vd_parent.childs.count(), 0)
        vd_child = VD(parent=vd_parent)
        vd_child.save()
        saved = VD.objects.all().order_by('-id')[0]
        self.assertEqual(vd_child, saved)
        self.assertEqual(saved.parent, vd_parent)
        self.assertEqual(vd_parent.childs.count(), 1)
        self.assertEqual(vd_parent.childs.first(), saved)

    def test_mask(self):
        vd = VD()
        vd.save()
        saved = VD.objects.first()
        self.assertEqual(saved.is_private, False)
        self.assertEqual(saved.is_public, False)
        self.assertEqual(saved.mask, 0 | 0)

        vd.is_private = True
        vd.is_public = False
        vd.save()
        saved = VD.objects.first()
        self.assertEqual(saved.is_private, True)
        self.assertEqual(saved.is_public, False)
        self.assertEqual(saved.mask, 0 | 1)

        vd.is_private = False
        vd.is_public = True
        vd.save()
        saved = VD.objects.first()
        self.assertEqual(saved.is_private, False)
        self.assertEqual(saved.is_public, True)
        self.assertEqual(saved.mask, 2 | 0)

    def test_send_email(self):
        if WORK_ENVIRONMENT: return
        r = send_email('gulby@naver.com', '유닛테스트', '유닛테스트임 http://www.daum.net/')
        self.assertEqual(r, True)

    def test_add_access_history(self):
        from place.models import UserPlace
        uplace1 = UserPlace.objects.create()
        uplace2 = UserPlace.objects.create()
        uplace3 = UserPlace.objects.create()
        vd = VD.objects.create()
        self.assertEqual(vd.accessHistory, None)
        vd.add_access_history(uplace1)
        self.assertEqual(len(vd.accessHistory['uplaces']), 1)
        self.assertIn(uplace1.uuid, json_dumps(vd.accessHistory['uplaces']))
        vd.add_access_history([uplace1, uplace2])
        self.assertEqual(len(vd.accessHistory['uplaces']), 3)
        self.assertIn(uplace1.uuid, json_dumps(vd.accessHistory['uplaces']))
        self.assertIn(uplace2.uuid, json_dumps(vd.accessHistory['uplaces']))
        self.assertNotIn(uplace3.uuid, json_dumps(vd.accessHistory['uplaces']))
        self.assertEqual(VD.objects.count(), 1)
        saved = VD.objects.first()
        self.assertEqual(saved, vd)
        self.assertDictEqual(saved.accessHistory, vd.accessHistory)


class StorageTest(FunctionalTestAfterLoginBase):

    def test_save_and_retreive(self):
        vd = VD.objects.get(id=self.vd_id)
        storage = Storage()
        storage.vd = vd
        storage.key = 'test_key'
        storage.value = {'test_sub_key': 'test_value'}
        storage.save()

        self.assertEqual(Storage.objects.count(), 1)
        saved = Storage.objects.first()
        self.assertEqual(saved, storage)
        self.assertEqual(saved.key, 'test_key')
        self.assertDictEqual(saved.value, {'test_sub_key': 'test_value'})

        storage2 = Storage()
        storage2.vd = vd
        storage2.key = 'other_key'
        storage2.value = {'test_sub_key': 'test_value'}
        storage2.save()
        self.assertEqual(Storage.objects.count(), 2)
        self.assertNotEqual(storage2, storage)

    def test_unique(self):
        vd = VD.objects.get(id=self.vd_id)
        storage = Storage.objects.create(vd=vd, key='key')
        with self.assertRaises(IntegrityError):
            storage2 = Storage.objects.create(vd=vd, key='key')


class TrackingTest(FunctionalTestAfterLoginBase):

    def test_save_and_retreive(self):
        lonLat = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        timestamp = get_timestamp()
        vd_id = self.vd_id
        vd = VD.objects.get(id=vd_id)
        self.assertEqual(Tracking.objects.count(), 0)
        tracking = Tracking.create(vd_id, lonLat, timestamp)
        self.assertEqual(Tracking.objects.count(), 1)
        self.assertEqual(tracking.vd_id, vd_id)
        self.assertEqual(tracking.created, timestamp)
        self.assertEqual(tracking.vd, vd)

        saved = Tracking.objects.first()
        self.assertEqual(saved, tracking)
        self.assertEqual(saved.vd_id, vd_id)
        self.assertEqual(saved.created, timestamp)
        self.assertEqual(saved.vd, vd)

    def test_string_representation(self):
        lonLat = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        timestamp = get_timestamp()
        vd_id = self.vd_id
        tracking = Tracking.create(vd_id, lonLat, timestamp)
        self.assertEqual(unicode(tracking), "VD(id=%d)'s Tracking(lat=%0.6f, lon=%0.6f)" % (vd_id, lonLat.y, lonLat.x))
