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
