#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import APITestBase
from content import models


class LegacyPlaceViewsetTest(APITestBase):

    def setUp(self):
        super(LegacyPlaceViewsetTest, self).setUp()
        self.lp, is_created = models.LegacyPlace.get_or_create_smart('4ccffc63f6378cfaace1b1d6.4square')
        self.lp.save()

    def test_list(self):
        response = self.client.get('/lps/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        lp2, is_created = models.LegacyPlace.get_or_create_smart('http://place.map.daum.net/15738374')
        response = self.client.get('/lps/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.LegacyPlace.objects.count())
        response = self.client.post('/lps/', dict(content=self.lp.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, models.LegacyPlace.objects.count())
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.lp.uuid)

        response = self.client.post('/lps/', dict(content='http://place.map.daum.net/15738374'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.LegacyPlace.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.lp.uuid)


class PhoneNumberViewsetTest(APITestBase):

    def setUp(self):
        super(PhoneNumberViewsetTest, self).setUp()
        self.phone, is_created = models.PhoneNumber.get_or_create_smart('010-5475-9245')
        self.phone.save()

    def test_list(self):
        response = self.client.get('/phones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        phone2, is_created = models.PhoneNumber.get_or_create_smart('010-5686-1613')
        response = self.client.get('/phones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.PhoneNumber.objects.count())
        response = self.client.post('/phones/', dict(content=self.phone.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.PhoneNumber.objects.count(), 1)
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.phone.uuid)

        response = self.client.post('/phones/', dict(content='010-5686-1613'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.PhoneNumber.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.phone.uuid)


class PlaceNameViewsetTest(APITestBase):

    def setUp(self):
        super(PlaceNameViewsetTest, self).setUp()
        self.pname, is_created = models.PlaceName.get_or_create_smart('능이향기')
        self.pname.save()

    def test_list(self):
        response = self.client.get('/pnames/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        pname2, is_created = models.PlaceName.get_or_create_smart('방아깐')
        response = self.client.get('/pnames/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.PlaceName.objects.count())
        response = self.client.post('/pnames/', dict(content=self.pname.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.PlaceName.objects.count(), 1)
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.pname.uuid)

        response = self.client.post('/pnames/', dict(content='방아깐'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.PlaceName.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.pname.uuid)


class AddressViewsetTest(APITestBase):

    def setUp(self):
        super(AddressViewsetTest, self).setUp()
        self.addr, is_created = models.Address.get_or_create_smart('경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)')
        self.addr.save()

    def test_list(self):
        response = self.client.get('/addrs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        addr2, is_created = models.Address.get_or_create_smart('경기도 하남시 풍산로 270 미사강변도시2단지 206동 402호')
        response = self.client.get('/addrs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.Address.objects.count())
        response = self.client.post('/addrs/', dict(content=self.addr.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.Address.objects.count(), 1)
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.addr.uuid)

        response = self.client.post('/addrs/', dict(content='경기도 하남시 풍산로 270 미사강변도시2단지 206동 402호'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.Address.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.addr.uuid)


class PlaceNoteViewsetTest(APITestBase):

    def setUp(self):
        super(PlaceNoteViewsetTest, self).setUp()
        self.pnote, is_created = models.PlaceNote.get_or_create_smart('능이백숙 국물 죽임~ ㅋ')
        self.pnote.save()

    def test_list(self):
        response = self.client.get('/pnotes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        pnote2, is_created = models.PlaceNote.get_or_create_smart('여긴 국물이 끝내줌')
        pnote2.save()
        response = self.client.get('/pnotes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.PlaceNote.objects.count())
        response = self.client.post('/pnotes/', dict(content=self.pnote.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.PlaceNote.objects.count(), 1)
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.pnote.uuid)

        response = self.client.post('/pnotes/', dict(content='여긴 국물이 끝내줌'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.PlaceNote.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.pnote.uuid)


class ImageNoteViewsetTest(APITestBase):

    def setUp(self):
        super(ImageNoteViewsetTest, self).setUp()
        self.inote, is_created = models.ImageNote.get_or_create_smart('자기랑 진우랑 찰칵 ^^')
        self.inote.save()

    def test_list(self):
        response = self.client.get('/inotes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        inote2, is_created = models.ImageNote.get_or_create_smart('진우^^')
        inote2.save()
        response = self.client.get('/inotes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)

    def test_create(self):
        self.assertEqual(1, models.ImageNote.objects.count())
        response = self.client.post('/inotes/', dict(content=self.inote.content))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.ImageNote.objects.count(), 1)
        result = json_loads(response.content)
        self.assertIn('uuid', result)
        self.assertNotIn('id', result)
        self.assertEqual(result['uuid'], self.inote.uuid)

        response = self.client.post('/inotes/', dict(content='진우^^'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.ImageNote.objects.count(), 2)
        result = json_loads(response.content)
        self.assertNotEqual(result['uuid'], self.inote.uuid)

