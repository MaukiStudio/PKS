#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from rest_framework import status

from base.tests import AdminTestCase, FunctionalTestBase
from place.models import UserPlace
from pks.settings import WORK_ENVIRONMENT


class IndexTest(AdminTestCase):

    def test_connect(self):
        response = self.client.get('/admin2/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('PlaceKoob Custom Admin - Home', response.content.decode('utf-8'))


class IndexTestNotLogin(FunctionalTestBase):

    def test_connect(self):
        self.assertNotLogin()
        self.assertVdNotLogin()
        response = self.client.get('/admin2/')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/admin/login/?next=/admin2/')


class PlacedTest(AdminTestCase):

    def test_connect(self):
        response = self.client.get('/admin2/placed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('PlaceKoob Custom Admin - Placed', response.content.decode('utf-8'))


class PlacedDetailTest1(AdminTestCase):

    def setUp(self):
        super(PlacedDetailTest1, self).setUp()
        json_add = '''
            {
                "lonLat": {"lon": 127.103743, "lat": 37.399732},
                "images": [{"content": "http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg"}]
            }
        '''
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.uplace = UserPlace.objects.first()

    def test_connect(self):
        response = self.client.get('/admin2/placed/%s/' % self.uplace.uuid)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('lon=127.103743&amp;lat=37.399732', response.content.decode('utf-8'))

    def test_placed_by_kakao(self):
        self.assertEqual(self.uplace.place, None)
        lp_url = 'http://place.map.daum.net/15738374'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(url=lp_url))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)

    def test_placed_by_naver_disabled(self):
        self.assertEqual(self.uplace.place, None)
        lp_url = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(url=lp_url))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertEqual(self.uplace.place, None)

    def test_placed_by_foursquare(self):
        if WORK_ENVIRONMENT: return
        self.assertEqual(self.uplace.place, None)
        lp_url = 'https://foursquare.com/v/%EB%B0%A9%EC%95%84%EA%B9%90/4ccffc63f6378cfaace1b1d6'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(url=lp_url))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)

    def test_placed_by_google(self):
        if WORK_ENVIRONMENT: return
        self.assertEqual(self.uplace.place, None)
        lp_url = 'https://www.google.com/maps/place/Han+Ha+Rum+Korean+Restaurant/@22.3636765,113.4067433,9z/data=!4m8!1m2!2m1!1z7Iud64u5!3m4!1s0x34040056de2d51b3:0xae100fb893526bdf!8m2!3d22.2801408!4d114.182783'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(url=lp_url))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)

    def test_placed_by_placeName(self):
        self.assertEqual(self.uplace.place, None)
        placeName = '능이향기'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(placeName=placeName))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)

    def test_placed_by_placeName_lonLat(self):
        self.assertEqual(self.uplace.place, None)
        placeName = '사당삼겹살'
        raw_lonLat = 'https://report.map.naver.com/form.nhn?tab=map&bounds=37.4732692%2C126.9799704%2C37.4766689%2C126.9823672&lat=37.4749672&lng=126.9811688&dlevel=13&enc=b64'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(placeName=placeName, lonLat=raw_lonLat))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)
        self.assertAlmostEqual(self.uplace.place.lonLat.x, 126.9811688, delta=0.0001)
        self.assertAlmostEqual(self.uplace.place.lonLat.y, 37.4749672, delta=0.0001)


class PlacedDetailTest2(AdminTestCase):

    def setUp(self):
        super(PlacedDetailTest2, self).setUp()
        json_add = '{"urls": [{"content": "http://blog.naver.com/cmykhc/220689607363"}]}'
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.uplace = UserPlace.objects.first()

    def test_connect(self):
        response = self.client.get('/admin2/placed/%s/' % self.uplace.uuid)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('LonLat Required', response.content.decode('utf-8'))

    def test_placed_by_kakao(self):
        self.assertEqual(self.uplace.place, None)
        lp_url = 'http://place.map.daum.net/15738374'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(url=lp_url))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)

    def test_placed_by_naver_disabled(self):
        self.assertEqual(self.uplace.place, None)
        lp_url = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(url=lp_url))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertEqual(self.uplace.place, None)

    def test_placed_by_mango(self):
        self.assertEqual(self.uplace.place, None)
        lp_url = 'https://www.mangoplate.com/restaurants/f-YvkBx8IemC'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(url=lp_url))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)

    def test_placed_by_placeName(self):
        self.assertEqual(self.uplace.place, None)
        placeName = '능이향기'
        with self.assertRaises(NotImplementedError):
            self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(placeName=placeName))

    def test_placed_by_placeName_lonLat1(self):
        self.assertEqual(self.uplace.place, None)
        placeName = '사당삼겹살'
        raw_lonLat = 'https://report.map.naver.com/form.nhn?tab=map&bounds=37.4732692%2C126.9799704%2C37.4766689%2C126.9823672&lat=37.4749672&lng=126.9811688&dlevel=13&enc=b64'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(placeName=placeName, lonLat=raw_lonLat))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)
        self.assertAlmostEqual(self.uplace.place.lonLat.x, 126.9811688, delta=0.0001)
        self.assertAlmostEqual(self.uplace.place.lonLat.y, 37.4749672, delta=0.0001)

    def test_placed_by_placeName_lonLat2(self):
        self.assertEqual(self.uplace.place, None)
        placeName = '평가옥 판교점'
        raw_lonLat = 'http://map.naver.com/?dlevel=13&pinType=site&pinId=30840674&x=127.1064507&y=37.4009435&enc=b64'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(placeName=placeName, lonLat=raw_lonLat))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)
        self.assertAlmostEqual(self.uplace.place.lonLat.x, 127.1064507, delta=0.0001)
        self.assertAlmostEqual(self.uplace.place.lonLat.y, 37.4009435, delta=0.0001)

    def test_placed_by_placeName_lonLat3(self):
        self.assertEqual(self.uplace.place, None)
        placeName = 'Nanyodo Books'
        raw_lonLat = 'https://www.google.com/maps/place/Nanyodo+Books/@35.6951861,139.7589115,17z/data=!4m5!3m4!1s0x60188c105ea64a1f:0xe82f337cd2c02f24!8m2!3d35.6951861!4d139.7611002?hl=ko-KR'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(placeName=placeName, lonLat=raw_lonLat))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)
        self.assertAlmostEqual(self.uplace.place.lonLat.x, 139.7611002, delta=0.0001)
        self.assertAlmostEqual(self.uplace.place.lonLat.y, 35.6951861, delta=0.0001)

    def test_placed_by_placeName_lonLat4(self):
        self.assertEqual(self.uplace.place, None)
        placeName = 'Mahana Estates Ltd.'
        raw_lonLat = 'https://www.google.com/maps/place/Mahana+Estates+Ltd./@-41.2648843,173.0421782,17z/data=!3m1!4b1!4m5!3m4!1s0x6d3b9afa5010184b:0x719c450d4430d6e7!8m2!3d-41.2648843!4d173.0443669'
        response = self.client.post('/admin2/placed/%s/' % self.uplace.uuid, dict(placeName=placeName, lonLat=raw_lonLat))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.uplace = UserPlace.objects.first()
        self.assertNotEqual(self.uplace.place, None)
        self.assertAlmostEqual(self.uplace.place.lonLat.x, 173.0443669, delta=0.0001)
        self.assertAlmostEqual(self.uplace.place.lonLat.y, -41.2648843, delta=0.0001)


class PlacesTest(AdminTestCase):

    def test_connect(self):
        response = self.client.get('/admin2/places/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('PlaceKoob Custom Admin - Places', response.content.decode('utf-8'))
