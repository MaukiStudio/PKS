#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.db import IntegrityError

from base.tests import APITestBase
from importer.models import Proxy, Importer
from account.models import VD


class ProxyTest(APITestBase):

    def setUp(self):
        super(ProxyTest, self).setUp()
        self.vd = VD()
        self.vd.save()

    def test_string_representation(self):
        proxy = Proxy()
        proxy.vd = self.vd
        self.assertEqual(unicode(proxy), "%s's proxy" % unicode(self.vd))

    def test_save_and_retrieve(self):
        proxy = Proxy()
        proxy.vd = self.vd
        proxy.save()
        self.assertEqual(proxy.id, self.vd.id)
        self.assertEqual(proxy.vd_id, self.vd.id)
        saved = Proxy.objects.first()
        self.assertEqual(saved, proxy)
        self.assertEqual(saved.vd, proxy.vd)

    def test_vd_column_not_null(self):
        with self.assertRaises(IntegrityError):
            proxy = Proxy.objects.create(vd=None)

    def test_vd_column_unique(self):
        proxy = Proxy.objects.create(vd=self.vd)
        with self.assertRaises(IntegrityError):
            Proxy.objects.create(vd=self.vd)

    def test_guide_column(self):
        proxy = Proxy()
        proxy.vd = self.vd
        test_data = dict(type="album", source_vd=1)
        proxy.guide = test_data
        proxy.save()
        saved = Proxy.objects.first()
        self.assertEqual(saved.guide, test_data)
        proxy2 = Proxy()
        proxy2.vd = VD()
        proxy2.vd.save()
        proxy2.guide = test_data
        with self.assertRaises(IntegrityError):
            proxy2.save()


class ImporterTest(APITestBase):

    def setUp(self):
        super(ImporterTest, self).setUp()
        self.vd = VD()
        self.vd.save()
        self.proxy = Proxy()
        self.proxy.vd = VD()
        self.proxy.vd.save()
        self.proxy.save()
        self.imp = Importer()
        self.imp.publisher = self.proxy
        self.imp.subscriber = self.vd
        self.imp.save()

    def test_save_and_retrieve(self):
        saved = Importer.objects.first()
        self.assertEqual(saved, self.imp)
        self.assertEqual(saved.publisher, self.imp.publisher)
        self.assertEqual(saved.subscriber, self.imp.subscriber)

    def test_relationship(self):
        self.assertEqual(self.proxy.subscribers.first(), self.vd)
        self.assertEqual(self.proxy.importers.first(), self.imp)
        self.assertEqual(self.vd.proxies.first(), self.proxy)
        self.assertEqual(self.vd.importers.first(), self.imp)
