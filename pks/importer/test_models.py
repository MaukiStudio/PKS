#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.db import IntegrityError
from json import loads as json_loads

from base.tests import APITestBase
from importer.models import Proxy, Importer
from account.models import VD


class ProxyTest(APITestBase):

    def setUp(self):
        super(ProxyTest, self).setUp()
        self.vd = VD.objects.create()
        self.test_guide = '{"type": "images", "vd": "myself"}'
        self.proxy = Proxy.objects.create(vd=self.vd, guide=self.test_guide)

    def test_string_representation(self):
        self.assertEqual(unicode(self.proxy), "%s's proxy" % unicode(self.vd))

    def test_save_and_retrieve(self):
        self.assertEqual(self.proxy.id, self.vd.id)
        self.assertEqual(self.proxy.vd_id, self.vd.id)
        saved = Proxy.objects.first()
        self.assertEqual(saved, self.proxy)
        self.assertEqual(saved.vd, self.proxy.vd)

    def test_vd_column_not_null(self):
        with self.assertRaises(IntegrityError):
            proxy2 = Proxy.objects.create(vd=None)

    def test_vd_column_unique(self):
        with self.assertRaises(IntegrityError):
            Proxy.objects.create(vd=self.vd)

    def test_guide_column(self):
        self.assertEqual(self.proxy.guide, json_loads(self.test_guide))
        saved = Proxy.objects.first()
        self.assertEqual(saved.guide, json_loads(self.test_guide))
        proxy2 = Proxy()
        proxy2.vd = VD()
        proxy2.vd.save()
        test_data2 = '{"vd": "myself", "type": "images"}'
        proxy2.guide = test_data2
        with self.assertRaises(IntegrityError):
            proxy2.save()

    def test_reload(self):
        proxy2 = Proxy.objects.get(id=self.proxy.id)
        self.proxy.started = 1
        self.proxy.save()
        self.assertEqual(proxy2, self.proxy)
        self.assertNotEqual(proxy2.started, self.proxy.started)
        proxy2 = proxy2.reload()
        self.assertEqual(proxy2, self.proxy)
        self.assertEqual(proxy2.started, self.proxy.started)


class ImporterTest(APITestBase):

    def setUp(self):
        super(ImporterTest, self).setUp()
        self.subscriber = VD.objects.create()
        self.publisher_vd = VD.objects.create()
        self.proxy = Proxy.objects.create(vd=self.publisher_vd)
        self.imp = Importer.objects.create(publisher=self.proxy, subscriber=self.subscriber)

    def test_save_and_retrieve(self):
        saved = Importer.objects.first()
        self.assertEqual(saved, self.imp)
        self.assertEqual(saved.publisher, self.imp.publisher)
        self.assertEqual(saved.subscriber, self.imp.subscriber)

    def test_relationship(self):
        self.assertEqual(self.proxy.subscribers.first(), self.subscriber)
        self.assertEqual(self.proxy.importers.first(), self.imp)
        self.assertEqual(self.subscriber.proxies.first(), self.proxy)
        self.assertEqual(self.subscriber.importers.first(), self.imp)

    def test_reload(self):
        imp2 = Importer.objects.get(id=self.imp.id)
        self.imp.started = 1
        self.imp.save()
        self.assertEqual(imp2, self.imp)
        self.assertNotEqual(imp2.started, self.imp.started)
        imp2 = imp2.reload()
        self.assertEqual(imp2, self.imp)
        self.assertEqual(imp2.started, self.imp.started)
