#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from rest_framework import status

from base.tests import FunctionalTestAfterLoginBase
from importer.models import Proxy, Importer
from account.models import VD


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
