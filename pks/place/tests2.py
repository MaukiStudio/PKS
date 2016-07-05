#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import APITestBase, FunctionalTestAfterLoginBase
from place.models import UserPlace, Place, PostPiece
from url.models import Url
from account.models import VD
from place.post import PostBase


class PlaceViewSetTest(FunctionalTestAfterLoginBase):

    def test_placed_by_url0(self):
        url, is_created = Url.get_or_create_smart('http://www.naver.com/')
        json_add = '''{"urls": [{"content": "%s"}]}''' % (url.content,)
        place1 = Place.objects.create()
        place2 = Place.objects.create()
        place3 = Place.objects.create()
        self.assertEqual(UserPlace.objects.count(), 0)

        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 0+1)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, None)

        url.add_place(place1)
        self.assertEqual(UserPlace.objects.count(), 1+0)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1+1)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, place1.id)

        url.add_place(place2)
        self.assertEqual(UserPlace.objects.count(), 2+2)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 4+1)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, None)

    def test_placed_by_url0_2(self):
        url, is_created = Url.get_or_create_smart('http://www.naver.com/')
        json_add = '''{"urls": [{"content": "%s"}]}''' % (url.content,)
        place1 = Place.objects.create()
        place2 = Place.objects.create()
        place3 = Place.objects.create()
        self.assertEqual(UserPlace.objects.count(), 0)

        pb = PostBase(json_add)
        uplace = UserPlace.objects.create(vd=self.vd)
        PostPiece.objects.create(place=None, uplace=uplace, vd=self.vd, pb=pb)

        url.add_place(place1)
        self.assertEqual(UserPlace.objects.count(), 1)
        '''
        pb = PostBase(json_add)
        uplace, is_created = UserPlace.get_or_create_smart(pb, self.vd)
        PostPiece.objects.create(place=None, uplace=uplace, vd=self.vd, pb=pb)
        print(is_created)
        #'''
        UserPlace.dump_all()
        #'''
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        uplace = UserPlace.get_from_uuid(json_loads(response.content)['uplace_uuid'])
        uplace.place = None
        uplace.save()
        #'''
        self.assertEqual(UserPlace.objects.count(), 1+1)
        UserPlace.dump_all()

        url.add_place(place2)
        self.assertEqual(UserPlace.objects.count(), 2+2)
        pb = PostBase(json_add)
        uplace = UserPlace.objects.create(vd=self.vd)
        PostPiece.objects.create(place=None, uplace=uplace, vd=self.vd, pb=pb)
        self.assertEqual(UserPlace.objects.count(), 4+1)

        url.add_place(place3)
        self.assertEqual(UserPlace.objects.count(), 5+1)
        pb = PostBase(json_add)
        uplace = UserPlace.objects.create(vd=self.vd)
        PostPiece.objects.create(place=None, uplace=uplace, vd=self.vd, pb=pb)
        self.assertEqual(UserPlace.objects.count(), 6+1)

    def test_placed_by_url1(self):
        url, is_created = Url.get_or_create_smart('http://www.naver.com/')
        json_add = '''{"urls": [{"content": "%s"}]}''' % (url.content,)
        place1 = Place.objects.create()
        place2 = Place.objects.create()
        place3 = Place.objects.create()
        self.assertEqual(UserPlace.objects.count(), 0)

        url.add_place(place1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 0+1)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, place1.id)

        url.add_place(place2)
        self.assertEqual(UserPlace.objects.count(), 1+2)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 3+1)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, None)

        url.add_place(place3)
        self.assertEqual(UserPlace.objects.count(), 4+1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 5+1)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, None)

    def test_placed_by_url2(self):
        url, is_created = Url.get_or_create_smart('http://www.naver.com/')
        json_add = '''{"urls": [{"content": "%s"}]}''' % (url.content,)
        place1 = Place.objects.create()
        place2 = Place.objects.create()
        place3 = Place.objects.create()
        place4 = Place.objects.create()
        self.assertEqual(UserPlace.objects.count(), 0)

        url.add_place(place1)
        url.add_place(place2)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 0+3)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, None)

        url.add_place(place3)
        self.assertEqual(UserPlace.objects.count(), 3+1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 4+1)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, None)

        url.add_place(place4)
        self.assertEqual(UserPlace.objects.count(), 5+1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 6+1)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, None)

    def test_placed_by_url3(self):
        url, is_created = Url.get_or_create_smart('http://www.naver.com/')
        json_add = '''{"urls": [{"content": "%s"}]}''' % (url.content,)
        place1 = Place.objects.create()
        place2 = Place.objects.create()
        place3 = Place.objects.create()
        place4 = Place.objects.create()
        self.assertEqual(UserPlace.objects.count(), 0)

        url.add_place(place1)
        url.add_place(place2)
        url.add_place(place3)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 0+4)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, None)

        url.add_place(place4)
        self.assertEqual(UserPlace.objects.count(), 4+1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 5+1)
        place_id = json_loads(response.content)['place_id']
        self.assertEqual(place_id, None)
