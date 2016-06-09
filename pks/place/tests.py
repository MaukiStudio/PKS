#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads, dumps as json_dumps
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from urllib import unquote_plus

from base.tests import APITestBase
from place.models import UserPlace, Place, PostPiece
from image.models import Image
from content.models import LegacyPlace, PhoneNumber, PlaceName, Address, PlaceNote, ImageNote
from url.models import Url
from account.models import VD
from place.post import PostBase
from base.legacy.urlnorm import norms
from pks.settings import WORK_ENVIRONMENT


class PlaceViewSetTest(APITestBase):

    def setUp(self):
        super(PlaceViewSetTest, self).setUp()
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.place = Place(); self.place.save()
        self.vd = VD.objects.first()
        self.uplace = UserPlace(vd=self.vd, place=self.place)
        self.uplace.save()

    def test_list(self):
        response = self.client.get('/places/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 1)
        self.assertIn('userPost', result['results'][0])
        self.assertIn('placePost', result['results'][0])

        point1 = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        point2 = GEOSGeometry('POINT(127.107316 37.400998)', srid=4326)
        response = self.client.get('/places/', dict(lon=point2.x, lat=point2.y, r=1000))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 0)

        self.place.lonLat = point1
        self.place.save()
        response = self.client.get('/places/', dict(lon=point2.x, lat=point2.y, r=1000))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        self.assertIn('lonLat', results[0])
        self.assertIn('lon', results[0]['lonLat'])
        self.assertIn('lat', results[0]['lonLat'])
        self.assertNotIn('placeName', results[0])
        self.assertNotIn('_totalPost', results[0])

        response = self.client.get('/places/', dict(lon=point2.x, lat=point2.y, r=100))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 0)

        place2 = Place()
        place2.lonLat = GEOSGeometry('POINT(127 37)', srid=4326)
        place2.save()
        place3 = Place()
        place3.lonLat = point2
        place3.save()
        response = self.client.get('/places/', dict(lon=point2.x, lat=point2.y, r=1000000))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['place_id'], place3.id)
        self.assertEqual(results[1]['place_id'], self.place.id)
        self.assertEqual(results[2]['place_id'], place2.id)

    def test_detail(self):
        response = self.client.get('/places/%s/' % self.place.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertNotIn('id', result)
        self.assertNotIn('vds', result)
        self.assertNotIn('placeName', result)
        self.assertNotIn('_totalPost', result)
        self.assertIn('place_id', result)
        self.assertIn('placePost', result)
        response = self.client.get('/places/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserPlaceViewSetTest(APITestBase):

    def setUp(self):
        super(UserPlaceViewSetTest, self).setUp()
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.place = Place(); self.place.save()
        self.vd = VD.objects.first()
        self.uplace = UserPlace(vd=self.vd)
        self.uplace.save()

    def test_regions(self):
        self.uplace.lonLat = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        self.uplace.save()
        response = self.client.get('/uplaces/regions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)
        self.assertEqual(len(results), 1)
        self.assertIn('lonLat', results[0])
        self.assertIn('count', results[0])
        self.assertIn('radius', results[0])

    def test_list(self):
        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        self.assertIn('userPost', results[0])
        self.assertIn('placePost', results[0])
        self.assertIn('created', results[0])
        self.assertIn('modified', results[0])
        self.assertIn('place_id', results[0])
        self.assertIn('uplace_uuid', results[0])
        self.assertIn('distance_from_origin', results[0])
        self.assertNotIn('id', results[0])
        self.assertNotIn('place', results[0])
        self.assertNotIn('vd', results[0])
        self.assertNotIn('mask', results[0])

        point1 = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        point2 = GEOSGeometry('POINT(127.107316 37.400998)', srid=4326)
        response = self.client.get('/uplaces/', dict(lon=point2.x, lat=point2.y, r=1000))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 0)

        self.uplace.lonLat = point1
        self.uplace.save()
        response = self.client.get('/uplaces/', dict(lon=point2.x, lat=point2.y, r=1000))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        response = self.client.get('/uplaces/', dict(lon=point2.x, lat=point2.y, r=100))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 0)

        uplace2 = UserPlace(vd=self.vd)
        uplace2.lonLat = GEOSGeometry('POINT(127 37)', srid=4326)
        uplace2.save()
        uplace3 = UserPlace(vd=self.vd)
        uplace3.lonLat = point2
        uplace3.save()
        response = self.client.get('/uplaces/', dict(lon=point2.x, lat=point2.y, r=0))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['uplace_uuid'], uplace3.uuid)
        self.assertEqual(results[1]['uplace_uuid'], self.uplace.uuid)
        self.assertEqual(results[2]['uplace_uuid'], uplace2.uuid)

        uplace_drop = UserPlace.objects.create(is_drop=True, vd=self.vd, lonLat=point2)
        response = self.client.get('/uplaces/', dict(lon=point2.x, lat=point2.y, r=0))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 3)

        # order_by
        response = self.client.get('/uplaces/', dict(lon=point2.x, lat=point2.y, r=0, order_by='distance_from_origin', limit=20, offset=0))
        results = json_loads(response.content)['results']
        self.assertEqual(results[0]['uplace_uuid'], uplace3.uuid)
        response = self.client.get('/uplaces/', dict(lon=point2.x, lat=point2.y, r=0, order_by='-distance_from_origin', limit=20, offset=0))
        results = json_loads(response.content)['results']
        self.assertEqual(results[0]['uplace_uuid'], uplace2.uuid)
        response = self.client.get('/uplaces/', dict(lon=point2.x, lat=point2.y, r=0, order_by='modified', limit=20, offset=0))
        results = json_loads(response.content)['results']
        self.assertEqual(results[0]['uplace_uuid'], self.uplace.uuid)
        response = self.client.get('/uplaces/', dict(lon=point2.x, lat=point2.y, r=0, order_by='-modified', limit=20, offset=0))
        results = json_loads(response.content)['results']
        self.assertEqual(results[0]['uplace_uuid'], uplace3.uuid)

        # placed
        response = self.client.get('/uplaces/', dict(placed=True))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 0)
        response = self.client.get('/uplaces/', dict(placed=False))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 3)

        # remove duplicated
        self.uplace.place = self.place
        self.uplace.save()
        uplace2.place = self.place
        uplace2.save()
        response = self.client.get('/uplaces/')
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 2)
        place2 = Place.objects.create()
        uplace3.place = place2
        uplace3.save()
        response = self.client.get('/uplaces/')
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 2)
        uplace3.place = self.place
        uplace3.save()
        response = self.client.get('/uplaces/')
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)


    def test_detail(self):
        response = self.client.get('/uplaces/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get('/uplaces/%s/' % self.uplace.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertIn('userPost', result)
        self.assertIn('placePost', result)
        self.assertNotIn('id', result)
        self.assertNotIn('mask', result)

        response2 = self.client.get('/uplaces/%s/' % self.uplace.uuid.split('.')[0])
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.content, response.content)

    def test_delete_not_placed(self):
        self.assertEqual(UserPlace.objects.count(), 1)
        response2 = self.client.delete('/uplaces/%s/' % self.uplace.uuid.split('.')[0])
        self.assertEqual(response2.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserPlace.objects.count(), 0)

    def test_delete_placed(self):
        self.uplace.place = self.place
        self.uplace.save()
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(PostPiece.objects.count(), 0)
        self.assertEqual(self.uplace.is_drop, False)
        response2 = self.client.delete('/uplaces/%s/' % self.uplace.uuid.split('.')[0])
        self.assertEqual(response2.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.uplace = UserPlace.objects.first()
        self.assertEqual(self.uplace.is_drop, True)
        self.assertEqual(PostPiece.objects.count(), 1)
        pp = PostPiece.objects.first()
        self.assertEqual(pp.uplace, self.uplace)
        self.assertEqual(pp.pb.notes[0].content, 'delete')

    def test_create_full(self):
        self.uplace.place = self.place
        self.uplace.save()

        #point1 = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        #point2 = GEOSGeometry('POINT(127.107316 37.400998)', srid=4326)
        point1 = GEOSGeometry('POINT(127.092557 37.390271)', srid=4326)
        point2 = GEOSGeometry('POINT(127.093557 37.391271)', srid=4326)
        qs11 = Place.objects.filter(lonLat__distance_lte=(point2, D(m=100)))
        self.assertEqual(len(qs11), 0)
        qs12 = Place.objects.filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs12), 0)
        qs2 = UserPlace.objects.filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs2), 0)
        qs3 = UserPlace.objects.filter(lonLat__distance_lte=(point2, D(m=100)))
        self.assertEqual(len(qs3), 0)
        qs4 = UserPlace.objects.filter(vd_id=self.vd.id).filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs4), 0)
        qs5 = UserPlace.objects.filter(vd_id=0).filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs5), 0)

        name1, is_created = PlaceName.get_or_create_smart('능라')
        addr11, is_created = Address.get_or_create_smart('경기도 성남시 분당구 산운로32번길 12')
        addr12, is_created = Address.get_or_create_smart('경기도 성남시 분당구 운중동 883-3')
        addr13, is_created = Address.get_or_create_smart('경기도 성남시 분당구 운중동')
        note11, is_created = PlaceNote.get_or_create_smart('분당 냉면 최고')
        note12, is_created = PlaceNote.get_or_create_smart('을밀대가 좀 더 낫나? ㅋ')
        note13, is_created = PlaceNote.get_or_create_smart('평양냉면')
        imgNote1, is_created = ImageNote.get_or_create_smart('냉면 사진')
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img2_content = 'http://blogpfthumb.phinf.naver.net/20100110_16/mardukas_1263055491560_VI01Ic_JPG/DSCN1968.JPG'
        img3_content = 'http://mblogthumb1.phinf.naver.net/20160302_36/mardukas_14569226823176xNHG_JPEG/DSC07314.JPG'
        img1, is_created = Image.get_or_create_smart(img1_content)
        img2, is_created = Image.get_or_create_smart(img2_content)
        img3, is_created = Image.get_or_create_smart(img3_content)
        url11, is_created = Url.get_or_create_smart('http://www.naver.com/')
        url12, is_created = Url.get_or_create_smart('http://www.naver.com/?2')
        url13, is_created = Url.get_or_create_smart('http://www.naver.com/?3')
        lp11, is_created = LegacyPlace.get_or_create_smart('4ccffc63f6378cfaace1b1d6.4square')
        lp12, is_created = LegacyPlace.get_or_create_smart('http://map.naver.com/local/siteview.nhn?code=21149144')
        lp13, is_created = LegacyPlace.get_or_create_smart('ChIJrTLr-GyuEmsRBfy61i59si0.google')
        phone1, is_created = PhoneNumber.get_or_create_smart('010-5597-9245')

        json_full = '''
            {
                "uplace_uuid": "%s",
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": "%s", "content": "%s"},
                "phone": {"uuid": "%s", "content": "%s"},
                "addr1": {"uuid": "%s", "content": "%s"},
                "addr2": {"uuid": "%s", "content": "%s"},
                "addr3": {"uuid": "%s", "content": "%s"},
                "notes": [
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null}
                ],
                "images": [
                    {"uuid": "%s", "content": "%s", "timestamp": null, "summary": "%s",
                        "note": {"uuid": "%s", "content": "%s", "timestamp": null}},
                    {"uuid": "%s", "content": "%s", "timestamp": null, "summary": "%s"},
                    {"uuid": "%s", "content": "%s", "timestamp": null, "summary": "%s"}
                ],
                "urls": [
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"}
                ],
                "lps": [
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"}
                ]
            }
        ''' % (self.uplace.uuid, point1.x, point1.y,
               name1.uuid, name1.content, phone1.uuid, phone1.content,
               addr11.uuid, addr11.content, addr12.uuid, addr12.content, addr13.uuid, addr13.content,
               note11.uuid, note11.content, note12.uuid, note12.content, note13.uuid, note13.content,
               img1.uuid, img1.content, img1.url_summarized, imgNote1.uuid, imgNote1.content,
               img2.uuid, img2.content, img2.url_summarized, img3.uuid, img3.content, img3.url_summarized,
               url11.uuid, url11.content, url12.uuid, url12.content, url13.uuid, url13.content,
               lp11.uuid, lp11.content, lp12.uuid, lp12.content, lp13.uuid, lp13.content,)
        want = PostBase(json_full)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_full))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 2)

        self.uplace = UserPlace.objects.first()
        want.normalize()
        self.uplace.userPost.normalize()
        self.assertIsSubsetOf(want, self.uplace.userPost)
        self.assertIsNotSubsetOf(self.uplace.userPost, want)
        self.assertIsSubsetOf(want, self.uplace.placePost)
        self.assertIsNotSubsetOf(self.uplace.placePost, want)

        result = json_loads(response.content)
        self.assertIn('created', result)
        self.assertIn('modified', result)
        t1 = result['modified']
        self.assertIn('place_id', result)
        self.assertIn('lonLat', result)
        self.assertIn('lon', result['lonLat'])
        self.assertIn('lat', result['lonLat'])
        result_userPost = result['userPost']
        result_placePost = result['placePost']
        self.assertDictEqual(result_userPost, self.uplace.userPost.json)
        self.assertDictEqual(result_placePost, self.uplace.placePost.json)

        # 한번 더...
        response = self.client.post('/uplaces/', dict(add=json_full))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 2)

        self.uplace = UserPlace.objects.first()
        want.normalize()
        self.uplace.userPost.normalize()
        self.assertIsSubsetOf(want, self.uplace.userPost)
        self.assertIsNotSubsetOf(self.uplace.userPost, want)
        self.assertIsSubsetOf(want, self.uplace.placePost)
        self.assertIsNotSubsetOf(self.uplace.placePost, want)

        result = json_loads(response.content)
        self.assertIn('created', result)
        self.assertIn('modified', result)
        t2 = result['modified']
        self.assertIn('place_id', result)
        self.assertIn('lonLat', result)
        self.assertIn('lon', result['lonLat'])
        self.assertIn('lat', result['lonLat'])
        result_userPost = result['userPost']
        result_placePost = result['placePost']

        self.printJson(result_userPost)
        self.printJson(self.uplace.userPost)
        self.assertDictEqual(result_userPost, self.uplace.userPost.json)
        self.assertDictEqual(result_placePost, self.uplace.placePost.json)

        self.assertGreater(t2, t1)
        self.assertAlmostEqual(t2, t1, delta=1000)

        # 삭제 포스트
        self.assertEqual(len(result_userPost['urls']), 3)
        json_remove = '{"urls": [{"content": "%s"}], "phone": {"content": "%s"}}' % (url12.content, phone1.content,)
        response = self.client.post('/uplaces/', dict(remove=json_remove, uplace_uuid=self.uplace.uuid))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 2)
        result = json_loads(response.content)
        prev_result_userPost = result_userPost
        result_userPost = result['userPost']
        prev_result_placePost = result_placePost
        result_placePost = result['placePost']
        self.assertEqual(result_placePost, prev_result_placePost)
        self.assertIsSubsetOf(result_userPost, prev_result_userPost)
        self.assertIsNotSubsetOf(prev_result_userPost, result_userPost)
        self.assertEqual(len(result_userPost['urls']), 2)
        result_userPost_str = json_dumps(result_userPost)
        self.assertIn(url11.content, result_userPost_str)
        self.assertNotIn(url12.content, result_userPost_str)
        self.assertIn(url13.content, result_userPost_str)
        self.assertNotIn(phone1.content, result_userPost_str)

        # 내장소 목록
        dummy_place = Place(); dummy_place.save()
        self.uplace._clearCache()
        response = self.client.get('/uplaces/?ru=myself')
        self.uplace._clearCache()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        result_userPost = results[0]['userPost']
        result_placePost = results[0]['placePost']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)
        self.assertDictEqual(result_userPost, self.uplace.userPost.json)
        self.assertDictEqual(result_placePost, self.uplace.placePost.json)

        qs11 = Place.objects.filter(lonLat__distance_lte=(point2, D(m=100)))
        self.assertEqual(len(qs11), 0)

        qs12 = Place.objects.filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs12), 1)
        self.assertEqual(UserPlace.objects.count(), 1)
        qs2 = UserPlace.objects.filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs2), 1)
        qs3 = UserPlace.objects.filter(lonLat__distance_lte=(point2, D(m=100)))
        self.assertEqual(len(qs3), 0)
        qs4 = UserPlace.objects.filter(vd_id=self.vd.id).filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs4), 1)
        qs5 = UserPlace.objects.filter(vd_id=0).filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs5), 0)


    def test_create_case1_current_pos_only_with_photo(self):
        point1 = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img1, is_created = Image.get_or_create_smart(img1_content)
        addr1_content = '경기도 성남시 분당구 산운로32번길 12'
        addr2_content = '경기도 성남시 분당구 운중동 883-3'

        json_add = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "images": [{"uuid": "%s", "content": null, "note": null}],
                "addr1": {"uuid": null, "content": "%s"},
                "addr2": {"uuid": null, "content": "%s"}
            }
        ''' % (point1.x, point1.y, img1.uuid, addr1_content, addr2_content,)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        self.assertEqual(Image.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 2)
        uplace = UserPlace.get_from_uuid(json_loads(response.content)['uplace_uuid'])
        self.assertEqual(Place.objects.count(), 1)

        self.assertEqual(Image.objects.count(), 1)
        img = Image.objects.first()
        self.assertEqual(img.lonLat, point1)
        self.assertEqual(img.timestamp, uplace.created - 1000)

        want = json_loads(json_add)
        self.assertIsSubsetOf(want, uplace.userPost)
        self.assertEqual(uplace.placePost, None)
        self.assertIsNotSubsetOf(uplace.userPost, want)

        point2 = GEOSGeometry('POINT(127.107316 37.400998)', srid=4326)
        self.assertEqual(Place.objects.count(), 1)
        qs11 = Place.objects.filter(lonLat__distance_lte=(point2, D(m=100)))
        self.assertEqual(len(qs11), 0)
        qs12 = Place.objects.filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs12), 0)
        qs2 = UserPlace.objects.filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs2), 1)
        qs3 = UserPlace.objects.filter(lonLat__distance_lte=(point2, D(m=100)))
        self.assertEqual(len(qs3), 0)
        qs4 = UserPlace.objects.filter(vd_id=self.vd.id).filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs4), 1)
        qs5 = UserPlace.objects.filter(vd_id=0).filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs5), 0)

        # 사진 추가
        uplace = UserPlace.objects.get(id=uplace.id)
        self.assertNotEqual(uplace.lonLat, None)
        img2_content = 'http://post.phinf.naver.net/20160503_211/1462272263200uaB94_JPEG/00%B8%DE%C0%CE%BB%E7%C1%F8.jpg?type=w1200'
        #img2_content = 'http://post.phinf.naver.net/20160329_169/dark861007_14592304554657EVx4_JPEG/dark861007_1081219906630853367.jpeg?type=f120_120'
        json_add = '''
            {
                "uplace_uuid": "%s",
                "images": [{"content": "%s"}]
            }
        ''' % (uplace.uuid, img2_content,)
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = json_loads(response.content)['userPost']
        print(result['images'][0]['content'])
        print(img2_content)
        self.assertEqual(result['images'][0]['content'], img2_content)

        uplace = UserPlace.objects.get(id=uplace.id)
        self.assertNotEqual(uplace.lonLat, None)

    def test_create_case2_current_pos_with_note_photo(self):
        point1 = GEOSGeometry('POINT(127 37)', srid=4326)
        note11, is_created = PlaceNote.get_or_create_smart('분당 냉면 최고')
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img1, is_created = Image.get_or_create_smart(img1_content)

        json_add = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "notes": [{"uuid": "%s", "content": null}],
                "images": [{"uuid": "%s", "content": null, "note": null}]
            }
        ''' % (point1.x, point1.y, note11.uuid, img1.uuid,)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)

        self.uplace = UserPlace.objects.first()
        want = json_loads(json_add)
        self.assertIsSubsetOf(want, self.uplace.userPost)
        self.assertEqual(self.uplace.placePost, None)
        self.assertIsNotSubsetOf(self.uplace.userPost, want)

    def test_create_case3_only_url(self):
        url1, is_created = Url.get_or_create_smart('http://m.blog.naver.com/mardukas/220671562152')

        json_add = '''
            {
                "urls": [{"uuid": "%s", "content": null}]
            }
        ''' % (url1.uuid,)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 2)
        self.assertEqual(Place.objects.count(), 1)

        uplace_uuid = json_loads(response.content)['uplace_uuid']
        self.uplace = UserPlace.objects.get(id=uplace_uuid.split('.')[0])
        want = json_loads(json_add)
        self.assertIsSubsetOf(want, self.uplace.userPost)
        self.assertEqual(self.uplace.placePost, None)
        self.assertIsNotSubsetOf(self.uplace.userPost, want)

    def test_create_case4_only_url_and_note(self):
        note11, is_created = PlaceNote.get_or_create_smart('분당 냉면 최고')
        url1, is_created = Url.get_or_create_smart('http://www.naver.com/')

        json_add = '''
            {
                "notes": [{"uuid": "%s", "content": null}],
                "urls": [{"uuid": "%s", "content": null}]
            }
        ''' % (note11.uuid, url1.uuid,)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)

        self.uplace = UserPlace.objects.first()
        want = json_loads(json_add)
        self.assertIsSubsetOf(want, self.uplace.userPost)
        self.assertEqual(self.uplace.placePost, None)
        self.assertIsNotSubsetOf(self.uplace.userPost, want)

    def test_create_case5_no_info(self):
        json_add = '''
            {
            }
        '''

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        with self.assertRaises(ValueError):
            response = self.client.post('/uplaces/', dict(add=json_add, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)

    def test_create_case6_complex_url(self):
        json_add = '''
            {
                "urls": [{"content": "%s"}]
            }
        ''' % ('https://m.map.naver.com/siteview.nhn?code=11523188&ret_url=https%3A%2F%2Fm.search.naver.com%2Fsearch.naver%3Fwhere%3Dm%26query%3D%25EC%259C%2584%25EB%258B%25B4%25ED%2595%259C%25EB%25B0%25A9%25EB%25B3%2591%25EC%259B%2590%26sm%3Dmsv_nex%23m_local',)
        json_want = '''
            {
                "urls": [{"content": "%s"}]
            }
        ''' % (norms('https://m.map.naver.com/siteview.nhn?code=11523188&ret_url=https%3A%2F%2Fm.search.naver.com%2Fsearch.naver%3Fwhere%3Dm%26query%3D%25EC%259C%2584%25EB%258B%25B4%25ED%2595%259C%25EB%25B0%25A9%25EB%25B3%2591%25EC%259B%2590%26sm%3Dmsv_nex%23m_local',))

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 2)
        self.assertEqual(Place.objects.count(), 2)

        uplace_uuid = json_loads(response.content)['uplace_uuid']
        self.uplace = UserPlace.objects.get(id=uplace_uuid.split('.')[0])
        want = json_loads(json_want)
        self.assertIsSubsetOf(want, self.uplace.userPost)
        self.assertNotEqual(self.uplace.placePost, None)
        self.assertIsNotSubsetOf(self.uplace.userPost, want)

        # again
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 3)
        self.assertEqual(Place.objects.count(), 2)

    def test_create_case7_4square_url(self):
        if WORK_ENVIRONMENT: return
        json_add = '''
            {
                "urls": [{"content": "%s"}]
            }
        ''' % ('DOREDORE (도레도레) - 하남대로 929 - http://4sq.com/MVWRaG',)
        json_want = '''
            {
                "urls": [{"content": "%s"}]
            }
        ''' % (norms('https://foursquare.com/v/doredore-도레도레/500d3737e4b03e92379f2714',))

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 2)
        self.assertEqual(Place.objects.count(), 2)

        uplace_uuid = json_loads(response.content)['uplace_uuid']
        self.uplace = UserPlace.objects.get(id=uplace_uuid.split('.')[0])
        want = json_loads(json_want)
        self.assertIsSubsetOf(want, self.uplace.userPost)
        self.assertNotEqual(self.uplace.placePost, None)
        self.assertIsNotSubsetOf(self.uplace.userPost, want)

        # again
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 3)
        self.assertEqual(Place.objects.count(), 2)


    def test_create_full_with_no_uuid_except_image(self):
        point1 = GEOSGeometry('POINT(127 37)', srid=4326)
        name1_content = '능라'
        addr1_content='경기도 성남시 분당구 운중동 883-3'
        note11_content='분당 냉면 최고'
        note12_content='을밀대가 좀 더 낫나? ㅋ'
        note13_content='평양냉면'
        imgNote1_content='냉면 사진'
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img2_content = 'http://blogpfthumb.phinf.naver.net/20100110_16/mardukas_1263055491560_VI01Ic_JPG/DSCN1968.JPG'
        img3_content = 'http://mblogthumb1.phinf.naver.net/20160302_36/mardukas_14569226823176xNHG_JPEG/DSC07314.JPG'
        img1, is_created = Image.get_or_create_smart(img1_content)
        img2, is_created = Image.get_or_create_smart(img2_content)
        img3, is_created = Image.get_or_create_smart(img3_content)
        url11_content='http://www.naver.com/'
        url12_content='http://www.naver.com/?2'
        url13_content='http://www.naver.com/?3'
        lp1, is_created = LegacyPlace.get_or_create_smart('4ccffc63f6378cfaace1b1d6.4square')

        json_add = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": null, "content": "%s"},
                "notes": [
                    {"uuid": null, "content": "%s"},
                    {"uuid": null, "content": "%s"},
                    {"uuid": null, "content": "%s"}
                ],
                "images": [
                    {"uuid": "%s", "content": null, "note": {"uuid": null, "content": "%s"}},
                    {"uuid": "%s", "content": null, "note": null},
                    {"uuid": "%s", "content": null, "note": null}
                ],
                "urls": [
                    {"uuid": null, "content": "%s"},
                    {"uuid": null, "content": "%s"},
                    {"uuid": null, "content": "%s"}
                ],
                "lps": [{"uuid": null, "content": "%s"}]
            }
        ''' % (point1.x, point1.y,
               name1_content,
               note11_content, note12_content, note13_content,
               img1.uuid, imgNote1_content, img2.uuid, img3.uuid,
               url11_content, url12_content, url13_content,
               lp1.content,)
        want = json_loads(json_add)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        self.assertEqual(self.uplace.place, None)
        response = self.client.post('/uplaces/', dict(add=json_add, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 2)

        self.uplace = UserPlace.objects.first()
        self.assertIsSubsetOf(want, self.uplace.userPost)
        self.assertIsNotSubsetOf(self.uplace.userPost, want)
        self.assertNotEqual(self.uplace.place, None)
        self.assertNotEqual(self.uplace.place, self.place)
        self.assertNotEqual(self.uplace.placePost, None)
        self.assertNotEqual(self.uplace.placePost.name, None)
        self.assertNotEqual(self.uplace.placePost.lonLat, None)

    def test_create_by_naver_map_url(self):
        self.uplace.place = self.place
        self.uplace.save()
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        lp.summarize()
        want = lp.content_summarized.json

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_dumps(want), uplace_uuid=self.uplace.uuid))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 2)

        # TODO : timestamp 만 살짝 차이 있는 경우에 대한 테스트는 어떻게?
        self.uplace = UserPlace.objects.first()
        self.assertIsSubsetOf(want, self.uplace.userPost)
        #self.assertIsSubsetOf(self.uplace.userPost, want)
        self.assertIsSubsetOf(want, self.uplace.placePost)
        #self.assertIsSubsetOf(self.uplace.placePost, want)
        #self.assertDictEqual(want, self.uplace.userPost.json)
        #self.printJson(self.uplace.userPost)
        #self.printJson(self.uplace.placePost)
        #self.assertDictEqual(self.uplace.userPost.json, self.uplace.placePost.json)

    def test_create_by_MAMMA(self):
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        json_add = '''
            {
                "urls": [{"content": "%s"}]
            }
        ''' % (test_data,)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 2)

        result_userPost = json_loads(response.content)['userPost']
        result_placePost = json_loads(response.content)['placePost']
        self.assertNotEqual(result_userPost['urls'][0], None)
        self.assertNotEqual(result_placePost['lonLat'], None)
        self.assertNotEqual(result_placePost['name'], None)
        self.assertNotEqual(result_placePost['phone'], None)
        self.assertNotEqual(result_placePost['addr1'], None)
        self.assertNotEqual(result_placePost['addr2'], None)
        self.assertNotEqual(result_placePost['lps'][0], None)

    def test_create_by_MAMMA2(self):
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        json_add = '''
            {
                "urls": [{"content": "%s"}]
            }
        ''' % (test_data,)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 2)
        self.assertEqual(Place.objects.count(), 2)

        result = json_loads(response.content)
        result_userPost = result['userPost']
        result_placePost = result['placePost']
        self.assertIn('lonLat', result)
        self.assertIn('lon', result['lonLat'])
        self.assertIn('lat', result['lonLat'])
        self.assertNotIn('uplace_uuid', result_userPost)
        self.assertNotIn('place_id', result_userPost)
        self.assertNotIn('uplace_uuid', result_placePost)
        self.assertNotIn('place_id', result_placePost)
        self.assertNotEqual(result_userPost['urls'][0], None)
        self.assertNotEqual(result_placePost['lonLat'], None)
        self.assertNotEqual(result_placePost['name'], None)
        self.assertNotEqual(result_placePost['phone'], None)
        self.assertNotEqual(result_placePost['addr1'], None)
        self.assertNotEqual(result_placePost['addr2'], None)
        self.assertNotEqual(result_placePost['lps'][0], None)

    def test_create_by_MAMMA3(self):
        test_data = 'http://place.kakao.com/places/14720610'
        json_add = '''
            {
                "urls": [{"content": "%s"}]
            }
        ''' % (test_data,)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 2)
        self.assertEqual(Place.objects.count(), 2)

        result = json_loads(response.content)
        result_userPost = result['userPost']
        result_placePost = result['placePost']
        self.assertIn('lonLat', result)
        self.assertIn('lon', result['lonLat'])
        self.assertIn('lat', result['lonLat'])
        self.assertNotIn('uplace_uuid', result_userPost)
        self.assertNotIn('place_id', result_userPost)
        self.assertNotIn('uplace_uuid', result_placePost)
        self.assertNotIn('place_id', result_placePost)
        self.assertNotEqual(result_userPost['urls'][0], None)
        self.assertNotEqual(result_placePost['lonLat'], None)
        self.assertNotEqual(result_placePost['name'], None)
        self.assertNotEqual(result_placePost['phone'], None)
        self.assertNotEqual(result_placePost['addr1'], None)
        self.assertNotEqual(result_placePost['addr2'], None)
        self.assertNotEqual(result_placePost['lps'][0], None)

    def test_create_by_MAMMA4(self):
        test_data = 'https://place.kakao.com/places/26955918'
        json_add = '''
            {
                "urls": [{"content": "%s"}]
            }
        ''' % (test_data,)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 2)
        self.assertEqual(Place.objects.count(), 2)

        result = json_loads(response.content)
        result_userPost = result['userPost']
        result_placePost = result['placePost']
        self.assertIn('lonLat', result)
        self.assertIn('lon', result['lonLat'])
        self.assertIn('lat', result['lonLat'])
        self.assertNotIn('uplace_uuid', result_userPost)
        self.assertNotIn('place_id', result_userPost)
        self.assertNotIn('uplace_uuid', result_placePost)
        self.assertNotIn('place_id', result_placePost)
        self.assertNotEqual(result_userPost['urls'][0], None)
        self.assertNotEqual(result_placePost['lonLat'], None)
        self.assertNotEqual(result_placePost['name'], None)
        self.assertNotIn('phone', result_placePost)
        self.assertNotEqual(result_placePost['addr1'], None)
        self.assertNotEqual(result_placePost['addr2'], None)
        self.assertNotEqual(result_placePost['lps'][0], None)

    def test_create_with_empty_note(self):
        json_add = '''
            {
                "urls": [{"content": "http://www.naver.com/"}],
                "notes": [{"content": ""}]
            }
        '''

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 2)
        self.assertEqual(Place.objects.count(), 1)

    def test_image_by_url(self):
        response = self.client.post('/uplaces/', dict(add='{"urls": [{"content": "http://map.naver.com/local/siteview.nhn?code=31130096"}]}'))
        result = json_loads(response.content)['userPost']['images'][0]['content']
        self.assertIn(result, [
            unquote_plus('https://ssl.map.naver.com/staticmap/image?version=1.1&crs=EPSG%3A4326&caller=og_map&center=127.0584149%2C37.3916387&level=11&scale=2&w=500&h=500&markers=type%2Cdefault2%2C127.0584149%2C37.3916387&baselayer=default'),
            'http://ldb.phinf.naver.net/20150902_90/1441122604108F2r99_JPEG/SUBMIT_1353817968111_31130096.jpg',
        ])

        response = self.client.post('/uplaces/', dict(add='{"urls": [{"content": "http://place.kakao.com/places/14720610"}]}'))
        result = json_loads(response.content)['userPost']['images'][0]['content']
        self.assertEqual(result, unquote_plus(
            'http://img1.daumcdn.net/thumb/C300x300/?fname=http%3A%2F%2Fdn-rp-place.kakao.co.kr%2Fplace%2FoWaiTZmpy7%2FviOeK5KRQK7mEsAHlckFgK%2FapreqCwxgnM_l.jpg'
        ))

        response = self.client.post('/uplaces/', dict(add='{"urls": [{"content": "http://m.blog.naver.com/mardukas/220671562152"}]}'))
        result = json_loads(response.content)['userPost']['images'][0]['content']
        self.assertEqual(result, 'http://blogthumb2.naver.net/20160401_292/mardukas_1459496453119PGXjg_JPEG/DSC03071.JPG?type=w2')


class PostPieceViewSetTest(APITestBase):

    def setUp(self):
        super(PostPieceViewSetTest, self).setUp()
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.place = Place()
        self.place.save()
        self.vd = VD.objects.first()
        self.uplace = UserPlace(vd=self.vd)
        self.uplace.save()
        self.pp = PostPiece(vd=self.vd, uplace=self.uplace)
        self.pp.save()

    def test_list(self):
        response = self.client.get('/pps/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        self.assertIn('data', results[0])

    def test_detail(self):
        response = self.client.get('/pps/%s/' % self.pp.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertIn('data', result)
        response = self.client.get('/pps/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
