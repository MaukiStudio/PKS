#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from rest_framework import status
from json import loads as json_loads

from base.tests import FunctionalTestAfterLoginBase
from importer.models import Importer, Proxy
from account.models import VD, RealUser
from base.utils import get_timestamp
from place.models import UserPlace, Place


class ImporterTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(ImporterTest, self).setUp()
        self.subscriber = VD.objects.get(id=self.vd_id)
        self.ru = RealUser.objects.create(email='gulby@naver.com')
        self.publisher_vd = VD.objects.create(deviceName='test device')
        self.proxy = Proxy.objects.create(vd=self.publisher_vd)
        self.imp = Importer.objects.create(publisher=self.proxy, subscriber=self.subscriber)

    def test_basic(self):
        guide_json = '{"type": "nothing"}'
        self.imp.publisher.guide = guide_json
        self.imp.publisher.save()
        ts = get_timestamp()
        r = self.imp.start()
        self.assertEqual(r.state, 'SUCCESS')
        self.assertEqual(r.result, True)
        self.imp = self.imp.reload()
        self.assertAlmostEqual(self.imp.started, ts, delta=1000)
        self.assertAlmostEqual(self.imp.ended, ts, delta=1000)
        self.assertGreater(self.imp.ended, self.imp.started)

    def test_import_user(self):
        publisher_vd1 = VD.objects.create(realOwner=self.ru)
        publisher_vd2 = VD.objects.create()
        place1 = Place.objects.create()
        uplace1 = UserPlace.objects.create(place=place1, vd=publisher_vd1)
        place2 = Place.objects.create()
        uplace2 = UserPlace.objects.create(place=place2, vd=publisher_vd2)

        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 0)

        guide_json = '{"type": "user", "email": "gulby@naver.com"}'
        self.imp.publisher.guide = guide_json
        self.imp.publisher.save()
        ts = get_timestamp()
        r = self.imp.start()
        self.assertEqual(r.state, 'SUCCESS')
        self.assertEqual(r.result, True)
        self.imp = self.imp.reload()
        self.assertAlmostEqual(self.imp.started, ts, delta=1000)
        self.assertAlmostEqual(self.imp.ended, ts, delta=1000)
        self.assertGreater(self.imp.ended, self.imp.started)

        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['iplace_uuid'], uplace1.uuid)

        publisher_vd2.realOwner = self.ru
        publisher_vd2.save()
        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 2)

    def test_import_images(self):
        # data 세팅

        # importer task test
        guide_json = '{"type": "images", "vd": "myself"}'
        self.imp.publisher.guide = guide_json
        self.imp.publisher.save()
        self.imp.publisher.vd.parent = self.subscriber
        self.imp.publisher.vd.save()
        ts = get_timestamp()
        r = self.imp.start()
        self.assertEqual(r.state, 'SUCCESS')
        self.assertEqual(r.result, True)
        self.imp = self.imp.reload()
        self.assertAlmostEqual(self.imp.started, ts, delta=1000)
        self.assertAlmostEqual(self.imp.ended, ts, delta=1000)
        self.assertGreater(self.imp.ended, self.imp.started)

        # proxy task test
        self.fail()
