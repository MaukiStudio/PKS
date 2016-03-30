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
