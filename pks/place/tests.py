#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads, dumps as json_dumps
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D

from base.tests import APITestBase
from place.models import UserPlace, Place, PostPiece
from image.models import Image
from content.models import LegacyPlace, PhoneNumber, PlaceName, Address, PlaceNote, ImageNote
from url.models import Url
from account.models import VD
from place.post import PostBase


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
        self.assertNotIn('userPost', result['results'][0])
        self.assertIn('placePost', result['results'][0])

        point1 = GEOSGeometry('POINT(127.1037430 37.3997320)')
        point2 = GEOSGeometry('POINT(127.107316 37.400998)')
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
        place2.lonLat = GEOSGeometry('POINT(127 37)')
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
        self.assertNotIn('id', results[0])
        self.assertNotIn('place', results[0])
        self.assertNotIn('vd', results[0])
        self.assertNotIn('mask', results[0])

        point1 = GEOSGeometry('POINT(127.1037430 37.3997320)')
        point2 = GEOSGeometry('POINT(127.107316 37.400998)')
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
        uplace2.lonLat = GEOSGeometry('POINT(127 37)')
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
        self.assertEqual(pp.data['notes'][0]['content'], 'delete')

    def test_create_full(self):
        self.uplace.place = self.place
        self.uplace.save()

        point1 = GEOSGeometry('POINT(127.1037430 37.3997320)')
        point2 = GEOSGeometry('POINT(127.107316 37.400998)')
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

        name1 = PlaceName(content='능라'); name1.save()
        addr11 = Address(content='경기도 성남시 분당구 산운로32번길 12'); addr11.save()
        addr12 = Address(content='경기도 성남시 분당구 운중동 883-3'); addr12.save()
        addr13 = Address(content='경기도 성남시 분당구 운중동'); addr13.save()
        note11 = PlaceNote(content='분당 냉면 최고'); note11.save()
        note12 = PlaceNote(content='을밀대가 좀 더 낫나? ㅋ'); note12.save()
        note13 = PlaceNote(content='평양냉면'); note13.save()
        imgNote1 = ImageNote(content='냉면 사진'); imgNote1.save()
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img2_content = 'http://blogpfthumb.phinf.naver.net/20100110_16/mardukas_1263055491560_VI01Ic_JPG/DSCN1968.JPG'
        img3_content = 'http://mblogthumb1.phinf.naver.net/20160302_36/mardukas_14569226823176xNHG_JPEG/DSC07314.JPG'
        img1 = Image(content=img1_content); img1.save()
        img2 = Image(content=img2_content); img2.save()
        img3 = Image(content=img3_content); img3.save()
        url11 = Url(content='http://www.naver.com/'); url11.save()
        url12 = Url(content='http://www.naver.com/?2'); url12.save()
        url13 = Url(content='http://www.naver.com/?3'); url13.save()
        lp11 = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square'); lp11.save()
        lp12 = LegacyPlace(content='http://map.naver.com/local/siteview.nhn?code=21149144'); lp12.save()
        lp13 = LegacyPlace(content='ChIJrTLr-GyuEmsRBfy61i59si0.google'); lp13.save()
        phone1 = PhoneNumber(content='010-5597-9245'); phone1.save()

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
        point1 = GEOSGeometry('POINT(127.1037430 37.3997320)')
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img1 = Image(content=img1_content); img1.save()
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
        response = self.client.post('/uplaces/', dict(add=json_add, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)

        self.uplace = UserPlace.objects.first()
        want = json_loads(json_add)
        self.assertIsSubsetOf(want, self.uplace.userPost)
        self.assertEqual(self.uplace.placePost, None)
        self.assertIsNotSubsetOf(self.uplace.userPost, want)

        point2 = GEOSGeometry('POINT(127.107316 37.400998)')
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

    def test_create_case2_current_pos_with_note_photo(self):
        point1 = GEOSGeometry('POINT(127 37)')
        note11 = PlaceNote(content='분당 냉면 최고'); note11.save()
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img1 = Image(content=img1_content); img1.save()

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
        url1 = Url(content='http://m.blog.naver.com/mardukas/220671562152'); url1.save()

        json_add = '''
            {
                "urls": [{"uuid": "%s", "content": null}]
            }
        ''' % (url1.uuid,)

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

    def test_create_case4_only_url_and_note(self):
        note11 = PlaceNote(content='분당 냉면 최고'); note11.save()
        url1 = Url(content='http://www.naver.com/'); url1.save()

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

    def test_create_full_with_no_uuid_except_image(self):
        point1 = GEOSGeometry('POINT(127 37)')
        name1_content = '능라'
        addr1_content='경기도 성남시 분당구 운중동 883-3'
        note11_content='분당 냉면 최고'
        note12_content='을밀대가 좀 더 낫나? ㅋ'
        note13_content='평양냉면'
        imgNote1_content='냉면 사진'
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img2_content = 'http://blogpfthumb.phinf.naver.net/20100110_16/mardukas_1263055491560_VI01Ic_JPG/DSCN1968.JPG'
        img3_content = 'http://mblogthumb1.phinf.naver.net/20160302_36/mardukas_14569226823176xNHG_JPEG/DSC07314.JPG'
        img1 = Image(content=img1_content); img1.save()
        img2 = Image(content=img2_content); img2.save()
        img3 = Image(content=img3_content); img3.save()
        url11_content='http://www.naver.com/'
        url12_content='http://www.naver.com?2'
        url13_content='http://www.naver.com?3'
        lp1 = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square'); lp1.save()

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
        lp = LegacyPlace()
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        lp.content = test_data
        lp.save()
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
        self.assertEqual(result, 'http://ldb.phinf.naver.net/20150902_90/1441122604108F2r99_JPEG/SUBMIT_1353817968111_31130096.jpg')

        response = self.client.post('/uplaces/', dict(add='{"urls": [{"content": "http://place.kakao.com/places/14720610"}]}'))
        result = json_loads(response.content)['userPost']['images'][0]['content']
        self.assertEqual(result, 'http://img1.daumcdn.net/thumb/C300x300/?fname=http%3A%2F%2Fdn-rp-place.kakao.co.kr%2Fplace%2FoWaiTZmpy7%2FviOeK5KRQK7mEsAHlckFgK%2FapreqCwxgnM_l.jpg')

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
