#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from django.contrib.gis.geos import GEOSGeometry

from base.tests import APITestBase
from place import models
from account.models import VD
from image.models import Image
from url.models import Url
from content.models import FsVenue, Note, Name, Address
from delorean import Delorean

BIT_ON_8_BYTE = int('0xFFFFFFFFFFFFFFFF', 16)
BIT_ON_6_BYTE = int('0x0000FFFFFFFFFFFF', 16)


class PlaceTest(APITestBase):

    def test_save_and_retreive(self):
        place = models.Place()
        place.save()
        saved = models.Place.objects.first()
        self.assertEqual(saved, place)

    def test_post(self):
        place = models.Place()
        place.save()

        vd1 = VD(); vd1.save()
        name1 = Name(content='능라'); name1.save()
        addr1 = Address(content='경기도 성남시 분당구 운중동 883-3'); addr1.save()
        note11 = Note(content='분당 냉면 최고'); note11.save()
        note12 = Note(content='만두도 괜찮음'); note12.save()
        img1 = Image(file=self.uploadImage('test.jpg')); img1.save()
        url1 = Url(url='http://maukistudio.com/'); url1.save()
        pc11 = models.PlaceContent(vd=vd1, place=place, name=name1, addr=addr1, note=note11, image=img1, url=url1); pc11.save()
        pc12 = models.PlaceContent(vd=vd1, place=place, lonLat=GEOSGeometry('POINT(127 37)'), note=note12); pc12.save()

        vd2 = VD(); vd2.save()
        name2 = Name(content='능라도'); name2.save()
        addr2 = Address(content='경기도 성남시 분당구 산운로32번길 12'); addr2.save()
        note21 = Note(content='여기 가게 바로 옆으로 이전'); note21.save()
        note22 = Note(content='평양냉면 맛집'); note22.save()
        img2 = Image(file=self.uploadImage('no_exif_test.jpg')); img2.save()
        url2 = Url(url='http://maukistudio.com/2'); url2.save()
        pc21 = models.PlaceContent(vd=vd2, place=place, name=name2, addr=addr2, note=note21, image=img2, url=url2); pc21.save()
        pc22 = models.PlaceContent(vd=vd2, place=place, lonLat=GEOSGeometry('POINT(127.1037430 37.3997320)'), note=note22); pc22.save()

        fsVenue = FsVenue(fsVenueId='40a55d80f964a52020f31ee3'); fsVenue.save()
        pc13 = models.PlaceContent(vd=vd1, place=place, fsVenue=fsVenue); pc13.save()

        want = json_loads('''
            {
                "id": %d,
                "latitude": %f,
                "longitude": %f,
                "name": "%s",
                "addr": "%s",
                "notes": ["%s", "%s", "%s", "%s"],
                "images": ["%s", "%s"],
                "urls": ["%s", "%s"],
                "fsVenue": "%s"
            }
        ''' % (place.id, 37.3997320, 127.1037430, name2, addr2, note22, note21, note12, note11,
               img2.file.url, img1.file.url, url2, url1, fsVenue,))
        self.assertDictEqual(place.post, want)


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
        self.assertEqual((int(pc.uuid) >> 16*8-2) & 1, 1)
        self.assertAlmostEqual((int(pc.uuid) >> 8*8-2) & BIT_ON_8_BYTE, d.epoch*1000, delta=1000)
        self.assertEqual((int(pc.uuid) >> 2*8-2) & BIT_ON_6_BYTE, self.vd.pk)
        saved = models.PlaceContent.objects.first()
        self.assertEqual(saved, pc)
        self.assertEqual(saved.uuid, pc.uuid)

    def test_uuid_property_with_no_vd(self):
        pc = models.PlaceContent()
        pc.save()
        self.assertEqual((int(pc.uuid) >> 2*8-2) & BIT_ON_6_BYTE, 0)

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

