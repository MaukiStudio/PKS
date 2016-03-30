#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.gis.geos import GEOSGeometry

from base.tests import APITestBase
from place import models
from account.models import VD
from image.models import Image
from url.models import Url
from content.models import FsVenue, Note, Name, Address
from delorean import Delorean


class PlaceTest(APITestBase):

    def test_save_and_retreive(self):
        place = models.Place()
        place.save()
        saved = models.Place.objects.first()
        self.assertEqual(saved, place)


class PlaceContentTest(APITestBase):

    def setUp(self):
        self.place = models.Place()
        self.place.save()
        self.vd = VD()
        self.vd.save()

        self.image = Image()
        self.image.file = self.uploadImage('test.jpg')
        self.image.save()
        self.url = Url(url='http://maukistudio.com/')
        self.url.save()

        self.fsVenue = FsVenue(fsVenueId='40a55d80f964a52020f31ee3')
        self.fsVenue.save()
        self.note = Note(content='맛집')
        self.note.save()
        self.name = Name(content='능라')
        self.name.save()
        self.addr = Address(content='경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)')
        self.addr.save()

    def test_save_and_retreive(self):
        pc = models.PlaceContent()
        pc.save()
        saved = models.PlaceContent.objects.first()
        self.assertEqual(saved, pc)

    def test_uuid_property(self):
        pc = models.PlaceContent(vd=self.vd)
        self.assertEqual(pc.uuid, None)
        d = Delorean()
        pc.save()
        self.assertNotEqual(pc.uuid, None)
        self.assertAlmostEqual((pc.uuid.__int__() >> 8*8) & int('0x00FFFFFFFFFFFFFF', 16), d.epoch*1000, delta=1000)
        self.assertEqual((pc.uuid.__int__() >> 2*8) & int('0x0000FFFFFFFFFFFF', 16), self.vd.pk)
        saved = models.PlaceContent.objects.first()
        self.assertEqual(saved, pc)
        self.assertEqual(saved.uuid, pc.uuid)

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

    def test_lonLat_property(self):
        pc = models.PlaceContent()
        point = GEOSGeometry('POINT(127.1037430 37.3997320)')
        pc.lonLat = point
        pc.save()
        saved = models.PlaceContent.objects.first()
        self.assertEqual(point, saved.lonLat)

    def test_image_property(self):
        pc = models.PlaceContent()
        pc.image = self.image
        pc.save()
        saved = self.image.pcs.get(pk=pc.pk)
        self.assertEqual(pc.image, self.image)
        self.assertEqual(pc.lonLat, None)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.image, self.image)
        self.assertEqual(saved.lonLat, None)

    def test_url_property(self):
        pc = models.PlaceContent()
        pc.url = self.url
        pc.save()
        saved = self.url.pcs.get(pk=pc.pk)
        self.assertEqual(pc.url, self.url)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.url, self.url)

    def test_fsVenue_property(self):
        pc = models.PlaceContent()
        pc.fsVenue = self.fsVenue
        pc.save()
        saved = self.fsVenue.pcs.get(pk=pc.pk)
        self.assertEqual(pc.fsVenue, self.fsVenue)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.fsVenue, self.fsVenue)

    def test_note_property(self):
        pc = models.PlaceContent()
        pc.note = self.note
        pc.save()
        saved = self.note.pcs.get(pk=pc.pk)
        self.assertEqual(pc.note, self.note)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.note, self.note)

    def test_name_property(self):
        pc = models.PlaceContent()
        pc.name = self.name
        pc.save()
        saved = self.name.pcs.get(pk=pc.pk)
        self.assertEqual(pc.name, self.name)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.name, self.name)

    def test_addr_property(self):
        pc = models.PlaceContent()
        pc.addr = self.addr
        pc.save()
        saved = self.addr.pcs.get(pk=pc.pk)
        self.assertEqual(pc.addr, self.addr)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.addr, self.addr)

