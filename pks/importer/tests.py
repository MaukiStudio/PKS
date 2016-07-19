#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from rest_framework import status
from json import loads as json_loads

from base.tests import FunctionalTestAfterLoginBase
from importer.models import Proxy, Importer, ImportedPlace
from account.models import VD, RealUser
from place.models import UserPlace, Place, PostPiece
from place.post import PostBase


class ProxyViewSetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(ProxyViewSetTest, self).setUp()
        self.proxy = Proxy()
        self.proxy.vd = VD.objects.get(id=self.vd_id)
        self.proxy.save()

    def test_list(self):
        response = self.client.get('/proxies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail(self):
        response = self.client.get('/proxies/%s/' % self.proxy.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BasicImporterViewSetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(BasicImporterViewSetTest, self).setUp()
        self.vd_publisher = VD()
        self.vd_publisher.save()
        self.proxy = Proxy()
        self.proxy.vd = self.vd_publisher
        self.proxy.save()
        self.vd_subscriber = VD.objects.get(id=self.vd_id)
        self.imp = Importer()
        self.imp.publisher = self.proxy
        self.imp.subscriber = self.vd_subscriber
        self.imp.save()

    def test_list(self):
        response = self.client.get('/importers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail(self):
        response = self.client.get('/importers/%s/' % self.imp.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_images1_basic(self):
        guide_json = '{"type": "images", "vd": "myself"}'
        response = self.client.post('/importers/', dict(guide=guide_json))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_images2_twice(self):
        guide_json = '{"type": "images", "vd": "myself"}'
        response = self.client.post('/importers/', dict(guide=guide_json))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Proxy.objects.count(), 2)
        self.assertEqual(Importer.objects.count(), 2)
        proxy = Proxy.objects.first()

        response = self.client.post('/importers/', dict(guide=guide_json))
        self.assertEqual(Proxy.objects.count(), 2)
        self.assertEqual(Importer.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_images3_importer_self(self):
        self.assertEqual(Proxy.objects.count(), 1)
        guide_json2 = '{"type": "images", "vd": %d}' % self.vd_subscriber.id
        proxy = Proxy.objects.create(vd=self.vd_subscriber, guide=guide_json2)
        self.assertEqual(Proxy.objects.count(), 2)
        response = self.client.post('/importers/', dict(guide=guide_json2))
        self.assertEqual(Proxy.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_images4_importer_private(self):
        self.assertEqual(Proxy.objects.count(), 1)
        guide_json2 = '{"type": "images", "vd": %d}' % self.vd_subscriber.id
        vd = VD()
        vd.is_private = True
        _vd = VD()
        _vd.save()
        vd.parent = _vd
        vd.save()
        proxy = Proxy.objects.create(vd=vd, guide=guide_json2)
        self.assertEqual(Proxy.objects.count(), 2)
        response = self.client.post('/importers/', dict(guide=guide_json2))
        self.assertEqual(Proxy.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ComplexImporterViewSetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(ComplexImporterViewSetTest, self).setUp()
        self.ru = RealUser.objects.create(email='gulby@naver.com')

    def test_create_user_importer(self):
        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 0)

        publisher_vd1 = VD.objects.create(realOwner=self.ru)
        publisher_vd2 = VD.objects.create()
        place1 = Place.objects.create()
        uplace1 = UserPlace.objects.create(place=place1, vd=publisher_vd1)
        place2 = Place.objects.create()
        uplace2 = UserPlace.objects.create(place=place2, vd=publisher_vd2)

        self.assertEqual(Proxy.objects.count(), 0)
        self.assertEqual(Importer.objects.count(), 0)
        self.assertEqual(VD.objects.count(), 3)
        guide_json = '{"type": "user", "email": "gulby@naver.com"}'
        response = self.client.post('/importers/', dict(guide=guide_json))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Proxy.objects.count(), 1)
        self.assertEqual(Importer.objects.count(), 1)
        self.assertEqual(VD.objects.count(), 4)

        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)

        publisher_vd2.realOwner = self.ru
        publisher_vd2.save()
        self.clear_cache(self.vd)

        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 2)


class ImportedPlaceViewSetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(ImportedPlaceViewSetTest, self).setUp()
        self.vd_subscriber = VD.objects.get(id=self.vd_id)
        self.vd_publisher = VD.objects.create()
        self.proxy = Proxy.objects.create(vd=self.vd_publisher)
        self.vd_publisher2 = VD.objects.create()
        self.proxy2 = Proxy.objects.create(vd=self.vd_publisher2)
        self.imp = Importer.objects.create(publisher=self.proxy, subscriber=self.vd_subscriber)
        self.imp2 = Importer.objects.create(publisher=self.proxy2, subscriber=self.vd_subscriber)
        self.place = Place.objects.create()
        self.place2 = Place.objects.create()
        self.iplace = ImportedPlace.objects.create(vd=self.vd_publisher, place=self.place)
        self.pb = PostBase('{"notes": [{"content": "test note"}]}')
        self.pp = PostPiece.create_smart(self.iplace, self.pb)
        self.iplace2 = ImportedPlace.objects.create(vd=self.vd_publisher, place=self.place2)
        self.iplace3 = ImportedPlace.objects.create(vd=self.vd_publisher, place=None)
        self.uplace = UserPlace.objects.create(vd=self.vd_subscriber, place=self.place2)
        self.vd_other = VD.objects.create()
        self.uplace_other = UserPlace.objects.create(vd=self.vd_other, place=self.place)
        self.place3 = Place.objects.create()
        self.iplace4 = UserPlace.objects.create(vd=self.vd_publisher2, place=self.place3)

    def test_list(self):
        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 2)
        self.assertIn('userPost', results[0])
        self.assertIn('placePost', results[0])
        self.assertIn('created', results[0])
        self.assertIn('modified', results[0])
        self.assertIn('place_id', results[0])
        self.assertIn('iplace_uuid', results[0])
        self.assertIn('distance_from_origin', results[0])
        self.assertNotIn('id', results[0])
        self.assertNotIn('uplace_uuid', results[0])
        self.assertNotIn('place', results[0])
        self.assertNotIn('vd', results[0])
        self.assertNotIn('mask', results[0])
        self.assertEqual(results[0]['iplace_uuid'], self.iplace4.uuid)
        self.assertEqual(results[1]['iplace_uuid'], self.iplace.uuid)
        self.iplace.computePost(self.vd_subscriber.realOwner_publisher_ids)
        self.assertNotEqual(self.iplace.userPost, None)
        self.assertIsSubsetOf(self.pb, self.iplace.userPost)
        self.assertNotEqual(results[1]['userPost'], None)
        self.assertDictEqual(results[1]['userPost'], self.iplace.userPost.cjson)

        # remove duplicate
        self.clear_cache(self.vd)
        self.iplace4.place = self.iplace.place
        self.iplace4.save()
        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)

    def test_detail(self):
        response = self.client.get('/iplaces/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get('/iplaces/%s/' % self.iplace.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertIn('userPost', result)
        self.assertIn('placePost', result)
        self.assertIn('created', result)
        self.assertIn('modified', result)
        self.assertIn('place_id', result)
        self.assertIn('iplace_uuid', result)
        self.assertIn('distance_from_origin', result)
        self.assertNotIn('id', result)
        self.assertNotIn('uplace_uuid', result)
        self.assertNotIn('place', result)
        self.assertNotIn('vd', result)
        self.assertNotIn('mask', result)
        self.assertEqual(result['iplace_uuid'], self.iplace.uuid)

        response2 = self.client.get('/iplaces/%s/' % self.iplace.uuid.split('.')[0])
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.content, response.content)

    def test_take(self):
        self.assertEqual(UserPlace.objects.count(), 6)
        response1 = self.client.post('/iplaces/%s/take/' % self.iplace.id)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 7)
        result1 = json_loads(response1.content)
        imported = UserPlace.objects.get(id=result1['uplace_uuid'].split('.')[0])
        self.assertEqual(imported, UserPlace.objects.all().order_by('-id')[0])
        self.assertIn('iplace_uuid', result1['userPost'])
        self.assertEqual(result1['userPost']['iplace_uuid'], self.iplace.uuid)
        self.assertIn('notes', result1['userPost'])
        self.assertEqual(result1['userPost']['notes'][0]['content'], 'test note')

        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)

    def test_drop(self):
        self.assertEqual(UserPlace.objects.count(), 6)
        response1 = self.client.post('/iplaces/%s/drop/' % self.iplace2.id)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(UserPlace.objects.count(), 6)

        self.assertEqual(UserPlace.objects.count(), 6)
        response1 = self.client.post('/iplaces/%s/drop/' % self.iplace.id)
        self.assertEqual(response1.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserPlace.objects.count(), 7)

        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
