#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from rest_framework import status
from json import loads as json_loads

from base.tests import FunctionalTestAfterLoginBase
from importer.models import Proxy, Importer, ImportedPlace
from account.models import VD
from place.models import UserPlace, Place


class ProxyViewSetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(ProxyViewSetTest, self).setUp()
        self.proxy = Proxy()
        self.proxy.vd = VD.objects.get(id=self.vd_id)
        self.proxy.save()

    def test_list(self):
        response = self.client.get('/proxies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail(self):
        response = self.client.get('/proxies/%s/' % self.proxy.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ImporterViewSetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(ImporterViewSetTest, self).setUp()
        self.vd_publisher = VD()
        self.vd_publisher.save()
        self.proxy = Proxy()
        self.proxy.vd = self.vd_publisher
        self.proxy.save()
        self.vd_subscriber = VD.objects.get(id=self.vd_id)
        self.imp = Importer()
        self.imp.publisher = self.proxy
        self.imp.subscriber = self.vd_subscriber
        self.imp.save()

    def test_list(self):
        response = self.client.get('/importers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail(self):
        response = self.client.get('/importers/%s/' % self.imp.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_images1_basic(self):
        guide_json = '{"type": "images", "vd": "myself"}'
        response = self.client.post('/importers/', dict(guide=guide_json))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_images2_twice(self):
        guide_json = '{"type": "images", "vd": "myself"}'
        response = self.client.post('/importers/', dict(guide=guide_json))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Proxy.objects.count(), 2)
        self.assertEqual(Importer.objects.count(), 2)
        proxy = Proxy.objects.first()

        response = self.client.post('/importers/', dict(guide=guide_json))
        self.assertEqual(Proxy.objects.count(), 2)
        self.assertEqual(Importer.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_images3_import_self(self):
        self.assertEqual(Proxy.objects.count(), 1)
        guide_json2 = '{"type": "images", "vd": %d}' % self.vd_subscriber.id
        proxy = Proxy.objects.create(vd=self.vd_subscriber, guide=guide_json2)
        self.assertEqual(Proxy.objects.count(), 2)
        response = self.client.post('/importers/', dict(guide=guide_json2))
        self.assertEqual(Proxy.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_images4_import_private(self):
        self.assertEqual(Proxy.objects.count(), 1)
        guide_json2 = '{"type": "images", "vd": %d}' % self.vd_subscriber.id
        vd = VD()
        vd.is_private = True
        _vd = VD()
        _vd.save()
        vd.parent = _vd
        vd.save()
        proxy = Proxy.objects.create(vd=vd, guide=guide_json2)
        self.assertEqual(Proxy.objects.count(), 2)
        response = self.client.post('/importers/', dict(guide=guide_json2))
        self.assertEqual(Proxy.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ImportedPlaceViewSetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(ImportedPlaceViewSetTest, self).setUp()
        self.vd_publisher = VD()
        self.vd_publisher.save()
        self.proxy = Proxy()
        self.proxy.vd = self.vd_publisher
        self.proxy.save()
        self.vd_subscriber = VD.objects.get(id=self.vd_id)
        self.imp = Importer()
        self.imp.publisher = self.proxy
        self.imp.subscriber = self.vd_subscriber
        self.imp.save()
        self.place = Place(); self.place.save()
        self.uplace = UserPlace(vd=self.vd_publisher)
        self.uplace.save()

    def test_list(self):
        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        self.assertIn('userPost', results[0])
        self.assertIn('placePost', results[0])
        self.assertIn('created', results[0])
        self.assertIn('modified', results[0])
        self.assertIn('place_id', results[0])
        self.assertNotIn('id', results[0])
        self.assertNotIn('place', results[0])
        self.assertNotIn('vd', results[0])


    def test_detail(self):
        response = self.client.get('/iplaces/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get('/iplaces/%s/' % self.uplace.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertIn('userPost', result)
        self.assertIn('placePost', result)
        self.assertNotIn('id', result)

        response2 = self.client.get('/iplaces/%s/' % self.uplace.uuid.split('.')[0])
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.content, response.content)
