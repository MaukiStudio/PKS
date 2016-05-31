#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from base.tests import APITestBase
from tag.models import Tag, UserPlaceTag, PlaceTag
from place.models import UserPlace, Place


class TagTest(APITestBase):

    def test_string_representation(self):
        tag = Tag()
        test_name = 'test tag'
        tag.name = test_name
        self.assertEqual(unicode(tag), test_name)

    def test_save_and_retreive(self):
        tag = Tag()
        test_name = 'test tag'
        tag.name = test_name
        self.assertEqual(Tag.objects.count(), 0)
        tag.save()
        self.assertEqual(Tag.objects.count(), 1)
        saved = Tag.objects.first()
        self.assertEqual(saved, tag)

    def test_value_property(self):
        tag = Tag()
        test_name = 'test tag'
        tag.name = test_name
        tag.save()
        saved = Tag.objects.first()
        self.assertEqual(tag.name, test_name)
        self.assertEqual(saved.name, test_name)


class UserPlaceTagTest(APITestBase):

    def setUp(self):
        super(UserPlaceTagTest, self).setUp()
        self.tag = Tag.objects.create(name='test tag')
        self.uplace = UserPlace.objects.create()

    def test_string_representation(self):
        uptag = UserPlaceTag()
        uptag.tag = self.tag
        uptag.uplace = self.uplace
        self.assertEqual(unicode(uptag), unicode(self.tag))

    def test_save_and_retreive(self):
        uptag = UserPlaceTag()
        uptag.tag = self.tag
        uptag.uplace = self.uplace
        self.assertEqual(UserPlaceTag.objects.count(), 0)
        uptag.save()
        self.assertEqual(UserPlaceTag.objects.count(), 1)
        saved = UserPlaceTag.objects.first()
        self.assertEqual(saved, uptag)


class PlaceTagTest(APITestBase):

    def setUp(self):
        super(PlaceTagTest, self).setUp()
        self.tag = Tag.objects.create(name='test tag')
        self.place = Place.objects.create()

    def test_string_representation(self):
        ptag = PlaceTag()
        ptag.tag = self.tag
        ptag.uplace = self.place
        self.assertEqual(unicode(ptag), unicode(self.tag))

    def test_save_and_retreive(self):
        ptag = PlaceTag()
        ptag.tag = self.tag
        ptag.uplace = self.place
        self.assertEqual(PlaceTag.objects.count(), 0)
        ptag.save()
        self.assertEqual(PlaceTag.objects.count(), 1)
        saved = PlaceTag.objects.first()
        self.assertEqual(saved, ptag)
