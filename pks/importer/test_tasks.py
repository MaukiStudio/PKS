#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from base.tests import APITestBase
from importer.models import Importer, Proxy
from account.models import VD
from base.utils import get_timestamp


class ImagesImporterTest(APITestBase):

    def setUp(self):
        super(ImagesImporterTest, self).setUp()
        self.subscriber = VD.objects.create()
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
