#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.db import IntegrityError

from base.tests import APITestBase
from tag.models import Tag, TagMatrix, UserPlaceTag, PlaceTag
from place.models import UserPlace, Place
from content.models import TagName


class TagTest(APITestBase):

    def test_string_representation(self):
        tag = Tag()
        tagName = TagName.get_from_json({'content': 'test tag'})
        tag.tagName = tagName
        self.assertEqual(unicode(tag), unicode(tagName))

    def test_save_and_retreive(self):
        tag = Tag()
        tagName = TagName.get_from_json({'content': 'test tag'})
        tag.tagName = tagName
        self.assertEqual(Tag.objects.count(), 0)
        tag.save()
        self.assertEqual(Tag.objects.count(), 1)
        saved = Tag.objects.first()
        self.assertEqual(saved, tag)

        tag2 = Tag()
        tag2.tagName = tagName
        with self.assertRaises(IntegrityError):
            tag2.save()

    def test_tagName_property(self):
        tag = Tag()
        tagName = TagName.get_from_json({'content': 'test tag'})
        tag.tagName = tagName
        tag.save()
        saved = Tag.objects.first()
        self.assertEqual(tag.tagName, tagName)
        self.assertEqual(saved.tagName, tagName)

    def test_prior_property(self):
        place1 = Place.objects.create()
        uplace1 = UserPlace.objects.create(place=place1)
        self.assertEqual(Place.objects.count(), 1)
        tag = Tag.objects.create(tagName=TagName.get_from_json({'content': 'test tag'}))
        self.assertAlmostEqual(tag.prior, (0+0.5)/(0+1.0), delta=0.000001)
        place2 = Place.objects.create()
        uplace2 = UserPlace.objects.create(place=place2)
        self.assertEqual(Place.objects.count(), 2)
        self.assertAlmostEqual(tag.prior, (0+0.5)/(0+1.0), delta=0.000001)

        self.assertEqual(tag.ptags.count(), 0)
        uptag1 = UserPlaceTag.objects.create(tag=tag, uplace=uplace1)
        self.assertEqual(tag.ptags.count(), 1)
        self.assertAlmostEqual(tag.prior, (1+0.5)/(1+1.0), delta=0.000001)
        uptag2 = UserPlaceTag.objects.create(tag=tag, uplace=uplace2)
        self.assertEqual(tag.ptags.count(), 2)
        self.assertAlmostEqual(tag.prior, (2+0.5)/(2+1.0), delta=0.000001)



class TagMatrixTest(APITestBase):

    def test_likelyhood_property(self):
        place1 = Place.objects.create()
        uplace1 = UserPlace.objects.create(place=place1)
        self.assertEqual(Place.objects.count(), 1)
        tag1 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'test tag'}))
        tag2 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other tag'}))
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (0 + (0+0.5)/(0+1.0))/(0+1), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (0 + (0+0.5)/(0+1.0))/(0+1), delta=0.000001)
        place2 = Place.objects.create()
        uplace2 = UserPlace.objects.create(place=place2)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (0 + (0+0.5)/(0+1.0))/(0+1), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (0 + (0+0.5)/(0+1.0))/(0+1), delta=0.000001)
        uptag1 = UserPlaceTag.objects.create(tag=tag1, uplace=uplace1)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (0 + (0+0.5)/(1+1.0))/(1+1), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (0 + (1+0.5)/(1+1.0))/(0+1), delta=0.000001)
        uptag2 = UserPlaceTag.objects.create(tag=tag2, uplace=uplace2)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (0 + (1+0.5)/(2+1.0))/(1+1), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (0 + (1+0.5)/(2+1.0))/(1+1), delta=0.000001)
        uptag11 = UserPlaceTag.objects.create(tag=tag1, uplace=uplace2)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (1 + (1+0.5)/(2+1.0))/(2+1), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (1 + (2+0.5)/(2+1.0))/(1+1), delta=0.000001)


class UserPlaceTagTest(APITestBase):

    def setUp(self):
        super(UserPlaceTagTest, self).setUp()
        self.tag = Tag.objects.create(tagName=TagName.get_from_json({'content': 'test tag'}))
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

        uptag2 = UserPlaceTag()
        uptag2.tag = self.tag
        uptag2.uplace = self.uplace
        with self.assertRaises(IntegrityError):
            uptag2.save()


class PlaceTagTest(APITestBase):

    def setUp(self):
        super(PlaceTagTest, self).setUp()
        self.tag = Tag.objects.create(tagName=TagName.get_from_json({'content': 'test tag'}))
        self.place = Place.objects.create()

    def test_string_representation(self):
        ptag = PlaceTag()
        ptag.tag = self.tag
        ptag.place = self.place
        self.assertEqual(unicode(ptag), unicode(self.tag))

    def test_save_and_retreive(self):
        ptag = PlaceTag()
        ptag.tag = self.tag
        ptag.place = self.place
        self.assertEqual(PlaceTag.objects.count(), 0)
        ptag.save()
        self.assertEqual(PlaceTag.objects.count(), 1)
        saved = PlaceTag.objects.first()
        self.assertEqual(saved, ptag)

        ptag2 = PlaceTag()
        ptag2.tag = self.tag
        ptag2.place = self.place
        with self.assertRaises(IntegrityError):
            ptag2.save()
