#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.test import TestCase

from place import models
from account.models import VD


class PlaceTest(TestCase):

    def test_save_and_retreive(self):
        place = models.Place()
        place.save()
        saved = models.Place.objects.first()
        self.assertEqual(saved, place)


class PlaceContentTest(TestCase):

    def setUp(self):
        self.place = models.Place()
        self.place.save()
        self.vd = VD()
        self.vd.save()
        self.image =

    def test_save_and_retreive(self):
        pc = models.PlaceContent()
        pc.save()
        saved = models.PlaceContent.objects.first()
        self.assertEqual(saved, pc)

    def test_place_property(self):
        pc = models.PlaceContent()
        pc.place = self.place
        pc.save()
        saved = self.place.pcs.get(pk=pc.pk)
        self.assertEqual(saved, pc)

    def test_vd_property(self):
        pc = models.PlaceContent()
        pc.vd = self.vd
        pc.save()
        saved = self.vd.pcs.get(pk=pc.pk)
        self.assertEqual(saved, pc)

    def test_core_property(self):
        pc = models.PlaceContent()
        pc.image =