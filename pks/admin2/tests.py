#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import AdminTestCase
from place.models import UserPlace


class IndexTest(AdminTestCase):

    def test_connect(self):
        response = self.client.get('/admin2/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('PlaceKoob Custom Admin - Home', response.content.decode('utf-8'))


class MappingTest(AdminTestCase):

    def test_connect(self):
        response = self.client.get('/admin2/mapping/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('PlaceKoob Custom Admin - Mapping', response.content.decode('utf-8'))


class MappingDetailTest1(AdminTestCase):

    def setUp(self):
        super(MappingDetailTest1, self).setUp()
        json_add = '''
            {
                "lonLat": {"lon": 127.1037430, "lat": 37.3997320},
                "images": [{"content": "http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg"}]
            }
        '''
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.uplace = UserPlace.objects.first()

    def test_mapping_by_lp_url(self):
        self.assertEqual(self.uplace.place, None)
        lp_url = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        response = self.client.post('/admin2/mapping/%s/' % self.uplace.uuid, dict(url=lp_url))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)

    def test_mapping_by_placeName(self):
        self.assertEqual(self.uplace.place, None)
        placeName = '능이향기'
        response = self.client.post('/admin2/mapping/%s/' % self.uplace.uuid, dict(placeName=placeName))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)

    def test_mapping_by_placeName_lonLat(self):
        self.assertEqual(self.uplace.place, None)
        placeName = '사당삼겹살'
        raw_lonLat = 'https://report.map.naver.com/form.nhn?tab=map&bounds=37.4732692%2C126.9799704%2C37.4766689%2C126.9823672&lat=37.4749672&lng=126.9811688&dlevel=13&enc=b64'
        response = self.client.post('/admin2/mapping/%s/' % self.uplace.uuid, dict(placeName=placeName, lonLat=raw_lonLat))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)
        self.assertAlmostEqual(self.uplace.place.lonLat.x, 126.9811688, delta=0.0001)
        self.assertAlmostEqual(self.uplace.place.lonLat.y, 37.4749672, delta=0.0001)


class MappingDetailTest2(AdminTestCase):

    def setUp(self):
        super(MappingDetailTest2, self).setUp()
        json_add = '''
            {
                "urls": [{"content": "http://blog.naver.com/cmykhc/220689607363"}]
            }
        '''
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.uplace = UserPlace.objects.first()

    def test_mapping_by_lp_url(self):
        self.assertEqual(self.uplace.place, None)
        lp_url = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        response = self.client.post('/admin2/mapping/%s/' % self.uplace.uuid, dict(url=lp_url))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)

    def test_mapping_by_placeName(self):
        self.assertEqual(self.uplace.place, None)
        placeName = '능이향기'
        with self.assertRaises(NotImplementedError):
            self.client.post('/admin2/mapping/%s/' % self.uplace.uuid, dict(placeName=placeName))

    def test_mapping_by_placeName_lonLat(self):
        self.assertEqual(self.uplace.place, None)
        placeName = '사당삼겹살'
        raw_lonLat = 'https://report.map.naver.com/form.nhn?tab=map&bounds=37.4732692%2C126.9799704%2C37.4766689%2C126.9823672&lat=37.4749672&lng=126.9811688&dlevel=13&enc=b64'
        response = self.client.post('/admin2/mapping/%s/' % self.uplace.uuid, dict(placeName=placeName, lonLat=raw_lonLat))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)
        self.assertAlmostEqual(self.uplace.place.lonLat.x, 126.9811688, delta=0.0001)
        self.assertAlmostEqual(self.uplace.place.lonLat.y, 37.4749672, delta=0.0001)
