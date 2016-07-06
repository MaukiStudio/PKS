#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.db import IntegrityError
from math import log

from base.tests import APITestBase
from tag.models import Tag, TagMatrix, UserPlaceTag, PlaceTag, PlaceNoteTag, ALPHA
from place.models import UserPlace, Place, PostPiece, PostBase
from content.models import TagName, PlaceNote
from account.models import VD


class TagTest(APITestBase):

    def test_string_representation(self):
        tag = Tag()
        tagName = TagName.get_from_json({'content': 'test tag'})
        tag.tagName = tagName
        self.assertEqual(unicode(tag), unicode(tagName))

    def test_save_and_retreive(self):
        tag = Tag()
        tagName, is_created = TagName.get_or_create_smart('test tag')
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
        tag, is_created = Tag.get_or_create_smart('test tag')
        self.assertAlmostEqual(tag.prior, (0+ALPHA*2)/(0+ALPHA*4), delta=0.000001)
        place2 = Place.objects.create()
        uplace2 = UserPlace.objects.create(place=place2)
        self.assertEqual(Place.objects.count(), 2)
        self.assertAlmostEqual(tag.prior, (0+ALPHA*2)/(0+ALPHA*4), delta=0.000001)

        self.assertEqual(tag.ptags.count(), 0)
        uptag1 = UserPlaceTag.objects.create(tag=tag, uplace=uplace1)
        self.assertEqual(tag.ptags.count(), 1)
        self.assertAlmostEqual(tag.prior, (1+ALPHA*2)/(1+ALPHA*4), delta=0.000001)
        uptag2 = UserPlaceTag.objects.create(tag=tag, uplace=uplace2)
        self.assertEqual(tag.ptags.count(), 2)
        self.assertAlmostEqual(tag.prior, (2+ALPHA*2)/(2+ALPHA*4), delta=0.000001)

    def test_tags_from_param(self):
        test_data = 'tag1 #tag2,tag3# #tag4, tag5#tag6 tag7'
        self.assertEqual(Tag.objects.count(), 0)
        tags = [tag.tagName.content for tag in Tag.tags_from_param(test_data)]
        self.assertIn('tag1', tags)
        self.assertIn('tag2', tags)
        self.assertIn('tag3', tags)
        self.assertIn('tag4', tags)
        self.assertIn('tag5', tags)
        self.assertNotIn('tag6', tags)
        self.assertNotIn('tag7', tags)
        self.assertIn('tag6tag7', tags)
        self.assertEqual(Tag.objects.count(), 6)


class TagMatrixTest(APITestBase):

    def __skip__test_likelyhood_property(self):
        place1 = Place.objects.create()
        uplace1 = UserPlace.objects.create(place=place1)
        self.assertEqual(Place.objects.count(), 1)
        tag1 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'test tag'}))
        tag2 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other tag'}))
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (0 + ALPHA)/(0+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (0 + ALPHA)/(0+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1)*tag1.prior, TagMatrix.likelyhood(tag1, tag2)*tag2.prior, delta=0.000001)
        place2 = Place.objects.create()
        uplace2 = UserPlace.objects.create(place=place2)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (0 + ALPHA)/(0+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (0 + ALPHA)/(0+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1)*tag1.prior, TagMatrix.likelyhood(tag1, tag2)*tag2.prior, delta=0.000001)
        uptag1 = UserPlaceTag.objects.create(tag=tag1, uplace=uplace1)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (0 + ALPHA)/(1+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (0 + ALPHA)/(0+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1)*tag1.prior, TagMatrix.likelyhood(tag1, tag2)*tag2.prior, delta=0.000001)
        uptag2 = UserPlaceTag.objects.create(tag=tag2, uplace=uplace2)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (0 + ALPHA)/(1+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (0 + ALPHA)/(1+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1)*tag1.prior, TagMatrix.likelyhood(tag1, tag2)*tag2.prior, delta=0.000001)
        uptag11 = UserPlaceTag.objects.create(tag=tag1, uplace=uplace2)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1), (1 + ALPHA)/(2+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag1, tag2), (1 + ALPHA)/(1+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood(tag2, tag1)*tag1.prior, TagMatrix.likelyhood(tag1, tag2)*tag2.prior, delta=0.000001)

    def __skip__test_likelyhood_negation_property(self):
        place1 = Place.objects.create()
        uplace1 = UserPlace.objects.create(place=place1)
        place2 = Place.objects.create()
        uplace2 = UserPlace.objects.create(place=place2)
        place3 = Place.objects.create()
        uplace3 = UserPlace.objects.create(place=place3)
        place4 = Place.objects.create()
        uplace4 = UserPlace.objects.create(place=place4)
        place5 = Place.objects.create()
        uplace5 = UserPlace.objects.create(place=place5)
        place6 = Place.objects.create()
        uplace6 = UserPlace.objects.create(place=place6)
        place7 = Place.objects.create()
        uplace7 = UserPlace.objects.create(place=place7)
        tag1 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'test tag'}))
        tag2 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other tag'}))
        tag3 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other3 tag'}))
        tag4 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other4 tag'}))
        tag5 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other5 tag'}))
        tag6 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other6 tag'}))
        tag7 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other7 tag'}))

        uptag1 = UserPlaceTag.objects.create(tag=tag1, uplace=uplace1)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag2, tag1), (0+ALPHA)/(0+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag1, tag2), (1+ALPHA)/(1+ALPHA*2), delta=0.000001)
        uptag2 = UserPlaceTag.objects.create(tag=tag2, uplace=uplace2)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag2, tag1), (1+ALPHA)/(1+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag1, tag2), (1+ALPHA)/(1+ALPHA*2), delta=0.000001)
        uptag11 = UserPlaceTag.objects.create(tag=tag1, uplace=uplace2)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag2, tag1), (0+ALPHA)/(0+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag1, tag2), (1+ALPHA)/(1+ALPHA*2), delta=0.000001)
        uptag3 = UserPlaceTag.objects.create(tag=tag3, uplace=uplace3)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag2, tag1), (0+ALPHA)/(1+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag1, tag2), (1+ALPHA)/(2+ALPHA*2), delta=0.000001)
        uptag4 = UserPlaceTag.objects.create(tag=tag4, uplace=uplace4)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag2, tag1), (0+ALPHA)/(2+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag1, tag2), (1+ALPHA)/(3+ALPHA*2), delta=0.000001)
        uptag5 = UserPlaceTag.objects.create(tag=tag5, uplace=uplace5)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag2, tag1), (0+ALPHA)/(3+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag1, tag2), (1+ALPHA)/(4+ALPHA*2), delta=0.000001)
        uptag6 = UserPlaceTag.objects.create(tag=tag6, uplace=uplace6)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag2, tag1), (0+ALPHA)/(4+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag1, tag2), (1+ALPHA)/(5+ALPHA*2), delta=0.000001)
        uptag7 = UserPlaceTag.objects.create(tag=tag7, uplace=uplace7)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag2, tag1), (0+ALPHA)/(5+ALPHA*2), delta=0.000001)
        self.assertAlmostEqual(TagMatrix.likelyhood_negation(tag1, tag2), (1+ALPHA)/(6+ALPHA*2), delta=0.000001)


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


class UserPlaceNLLTest(APITestBase):

    def setUp(self):
        super(UserPlaceNLLTest, self).setUp()
        self.place = Place.objects.create()
        self.vd = VD.objects.create()
        self.uplace = UserPlace.objects.create(place=self.place, vd=self.vd)
        self.tag = Tag.objects.create(tagName=TagName.get_from_json({'content': 'test tag'}))
        self.utag = UserPlaceTag.objects.create(tag=self.tag, uplace=self.uplace)

    def test_case1_user_tag(self):
        self.assertAlmostEqual(self.uplace.getNLL([self.tag]), 0.0)

    def test_case2_place_tag(self):
        uplace2 = UserPlace.objects.create(place=self.place)
        self.assertAlmostEqual(uplace2.getNLL([self.tag]), -log(0.833333), delta=0.000001)

    def test_case3_other_tag(self):
        place2 = Place.objects.create()
        uplace2 = UserPlace.objects.create(place=place2)
        tag2 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other tag'}))
        utag2 = UserPlaceTag.objects.create(tag=tag2, uplace=uplace2)
        self.assertAlmostEqual(uplace2.getNLL([self.tag]), 0.693147, delta=0.000001)

        place3 = Place.objects.create()
        uplace3 = UserPlace.objects.create(place=place3)
        self.assertAlmostEqual(uplace3.getNLL([self.tag]), uplace2.getNLL([self.tag]), delta=0.3)
        tag3 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other3 tag'}))
        utag3 = UserPlaceTag.objects.create(tag=tag3, uplace=uplace3)
        self.assertAlmostEqual(uplace3.getNLL([self.tag]), uplace2.getNLL([self.tag]), delta=0.000001)

    def test_case4_mix(self):
        uplace12 = UserPlace.objects.create(place=self.place)
        tag12 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other tag'}))
        utag12 = UserPlaceTag.objects.create(tag=tag12, uplace=uplace12)
        tag3 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other3 tag'}))
        tag4 = Tag.objects.create(tagName=TagName.get_from_json({'content': 'other4 tag'}))
        self.assertAlmostEqual(self.uplace.getNLL([self.tag, tag12, tag3, tag4]), 2.736450, delta=0.000001)
        self.assertAlmostEqual(self.uplace.getNLL([self.tag, tag12, tag3, tag4]),
                               self.uplace.getNLL([self.tag, tag12, tag3, tag4, tag4, self.tag, tag12]), delta=0.000001)


class PlaceNoteTagTest(APITestBase):

    def setUp(self):
        super(PlaceNoteTagTest, self).setUp()
        self.tag, is_created = Tag.get_or_create_smart('test tag')
        self.placeNote, is_created = PlaceNote.get_or_create_smart('test note')

    def test_string_representation(self):
        ctag = PlaceNoteTag()
        ctag.tag = self.tag
        ctag.placeNote = self.placeNote
        self.assertEqual(unicode(ctag), unicode(self.tag))

    def test_save_and_retreive(self):
        ctag = PlaceNoteTag()
        ctag.tag = self.tag
        ctag.placeNote = self.placeNote
        self.assertEqual(PlaceNoteTag.objects.count(), 0)
        ctag.save()
        self.assertEqual(PlaceNoteTag.objects.count(), 1)
        saved = PlaceNoteTag.objects.first()
        self.assertEqual(saved, ctag)

        ctag = PlaceNoteTag()
        ctag.tag = self.tag
        ctag.placeNote = self.placeNote
        with self.assertRaises(IntegrityError):
            ctag.save()

    def test_realtime_extract_tag_from_placeNote(self):
        self.assertEqual(Tag.objects.count(), 1+0)
        test_data = 'tag1 #tag2,tag3# #tag4 #tag5#tag6 tag7'
        placeNote2, is_created = PlaceNote.get_or_create_smart(test_data)
        self.assertEqual(Tag.objects.count(), 1+4)
        tags = [tag.tagName.content for tag in Tag.objects.all()]
        self.assertNotIn('tag1', tags)
        self.assertIn('tag2', tags)
        self.assertNotIn('tag3', tags)
        self.assertIn('tag4', tags)
        self.assertIn('tag5', tags)
        self.assertIn('tag6', tags)
        self.assertNotIn('tag7', tags)

    def test_realtime_extract_tag_from_placeNote2(self):
        self.assertEqual(Tag.objects.count(), 1+0)
        test_data = '[NOTE_TAGS]#["시골밥상","나물반찬","산사랑"]'
        placeNote2, is_created = PlaceNote.get_or_create_smart(test_data)
        self.assertEqual(Tag.objects.count(), 1+3)
        tags = [tag.tagName.content for tag in Tag.objects.all()]
        self.assertIn('시골밥상', tags)
        self.assertIn('나물반찬', tags)
        self.assertIn('산사랑', tags)

    def test_realtime_tagging_from_placeNote(self):
        place = Place.objects.create()
        uplace = UserPlace.objects.create(place=place)

        self.assertEqual(Tag.objects.count(), 1+0)
        # PostPiece 생성 구현...
        json = '''
            {
                "notes": [{"content": "tag1 #tag2# tag3# #tag4 #tag5#tag6 tag7"}]
            }
        '''
        pb = PostBase(json)
        pp = PostPiece.create_smart(uplace, pb)
        self.assertEqual(Tag.objects.count(), 1+4)

