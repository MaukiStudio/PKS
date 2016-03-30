#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1, UUID

from base.tests import APITestBase
from content import models


class FsVenueTest(APITestBase):

    def test_string_representation(self):
        fs = models.FsVenue()
        test_data = '40a55d80f964a52020f31ee3'
        fs.fsVenueId = test_data
        self.assertEqual(unicode(fs), test_data)

    def test_save_and_retreive(self):
        fs = models.FsVenue()
        fs.uuid = uuid1()
        fs.save()
        saved = models.FsVenue.objects.first()
        self.assertEqual(saved, fs)
        self.assertEqual(saved.uuid, fs.uuid)

    def test_fsVenueId_property(self):
        fs = models.FsVenue()
        test_data = '40a55d80f964a52020f31ee3'
        fs.fsVenueId = test_data
        fs.save()
        saved = models.FsVenue.objects.first()
        self.assertEqual(fs.fsVenueId, test_data)
        self.assertEqual(saved, fs)
        self.assertEqual(saved.uuid, fs.uuid)
        self.assertEqual(saved.fsVenueId, fs.fsVenueId)
        self.assertEqual(saved.uuid, UUID('00000000-40a5-5d80-f964-a52020f31ee3'))


class NoteTest(APITestBase):

    def test_string_representation(self):
        nt = models.Note()
        test_data = '맛집'
        nt.content = test_data
        self.assertEqual(unicode(nt), test_data)

    def test_save_and_retreive(self):
        nt = models.Note()
        nt.uuid = uuid1()
        nt.save()
        saved = models.Note.objects.first()
        self.assertEqual(saved, nt)
        self.assertEqual(saved.uuid, nt.uuid)

    def test_fsVenueId_property(self):
        nt = models.Note()
        test_data = '맛집'
        nt.content = test_data
        nt.save()
        saved = models.Note.objects.first()
        self.assertEqual(nt.content, test_data)
        self.assertEqual(saved, nt)
        self.assertEqual(saved.uuid, nt.uuid)
        self.assertEqual(saved.content, nt.content)


class NameTest(APITestBase):

    def test_string_representation(self):
        name = models.Name()
        test_data = '능라'
        name.content = test_data
        self.assertEqual(unicode(name), test_data)

    def test_save_and_retreive(self):
        name = models.Name()
        name.uuid = uuid1()
        name.save()
        saved = models.Name.objects.first()
        self.assertEqual(saved, name)
        self.assertEqual(saved.uuid, name.uuid)

    def test_fsVenueId_property(self):
        name = models.Name()
        test_data = '능라'
        name.content = test_data
        name.save()
        saved = models.Name.objects.first()
        self.assertEqual(name.content, test_data)
        self.assertEqual(saved, name)
        self.assertEqual(saved.uuid, name.uuid)
        self.assertEqual(saved.content, name.content)


class AddressTest(APITestBase):

    def test_string_representation(self):
        addr = models.Address()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr.content = test_data
        self.assertEqual(unicode(addr), test_data)

    def test_save_and_retreive(self):
        addr = models.Address()
        addr.uuid = uuid1()
        addr.save()
        saved = models.Address.objects.first()
        self.assertEqual(saved, addr)
        self.assertEqual(saved.uuid, addr.uuid)

    def test_fsVenueId_property(self):
        addr = models.Address()
        test_data = '경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)'
        addr.content = test_data
        addr.save()
        saved = models.Address.objects.first()
        self.assertEqual(addr.content, test_data)
        self.assertEqual(saved, addr)
        self.assertEqual(saved.uuid, addr.uuid)
        self.assertEqual(saved.content, addr.content)
