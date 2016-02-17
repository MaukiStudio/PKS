#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError

from strgen import StringGenerator as SG

from account import models


class VirtualDeviceSimpleTest(TestCase):

    def setUp(self):
        self.user = User()
        self.user.username = SG('[\w]{30}').render()
        self.user.password = SG('[\l]{6:10}&[\d]{2}').render()
        self.user.save()

        self.vd = models.VD()
        self.vd.name = SG('[\w\-]{36}').render()
        self.vd.user = self.user

    def test_save_and_retreive(self):
        self.vd.save()
        saved = models.VD.objects.all()[0]
        self.assertEqual(saved.name, self.vd.name)
        self.assertEqual(saved.user, self.user)

    def test_can_save_same_name(self):
        self.vd.save()
        vd2 = models.VD()
        vd2.name = self.vd.name
        vd2.save()
        self.assertNotEqual(self.vd, vd2)

    def test_cannot_save_same_user(self):
        self.vd.save()
        vd2 = models.VD()
        vd2.user = self.vd.user
        with self.assertRaises(IntegrityError):
            vd2.save()
