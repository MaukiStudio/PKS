#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from base.tests import APITestBase
from importer.tasks import ImagesImporter
from importer.models import Importer, Proxy
from account.models import VD


class ImagesImporterTest(APITestBase):

    def setUp(self):
        super(ImagesImporterTest, self).setUp()
        self.subscriber = VD.objects.create()
        self.publisher_vd = VD.objects.create(deviceName='test device')
        self.proxy = Proxy.objects.create(vd=self.publisher_vd)
        self.imp = Importer.objects.create(publisher=self.proxy, subscriber=self.subscriber)

    def test_basic(self):
        task = ImagesImporter()
        r = task.delay(self.imp)
        self.assertEqual(r.state, 'SUCCESS')
        self.assertEqual(r.result, 'test device')
