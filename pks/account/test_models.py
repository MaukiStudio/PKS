#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from strgen import StringGenerator as SG
from django.test import TestCase

from account import models


class VirtualDeviceSimpleTest(TestCase):

    def setUp(self):
        self.vd = models.VirtualDevice()
        self.vd.name = SG('[\w\-]{30}').render()

    def test_save_and_retreive(self):
        self.vd.save()
        self.assertEqual(models.VirtualDevice.objects.all()[0].name, self.vd.name)