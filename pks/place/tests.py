#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from time import sleep
from django.contrib.gis.measure import D

from base.tests import APITestBase
from place.models import UserPlace, Place
from image.models import Image
from content.models import ShortText, LegacyPlace, PhoneNumber
from url.models import Url
from account.models import VD
from place.post import Post


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
        response = self.client.get('/places/', dict(lon=point2.x, lat=point2.y, r=100))
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 0)

    def test_detail(self):
        response = self.client.get('/places/%s/' % self.place.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertNotIn('id', result)
        self.assertNotIn('vds', result)
        self.assertIn('place_id', result)
        self.assertIn('placePost', result)
        response = self.client.get('/places/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PlaceContentViewSetTest(APITestBase):

    def setUp(self):
        super(PlaceContentViewSetTest, self).setUp()
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})

    def test_list_no_place(self):
        response = self.client.get('/pcs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 0)


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
        self.uplace.save()
        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        self.assertIn('userPost', results[0])
        self.assertIn('placePost', results[0])
        self.assertIn('created', results[0])
        self.assertIn('modified', results[0])
        self.assertIn('place_id', results[0])
        self.assertNotIn('id', results[0])
        self.assertNotIn('place', results[0])
        self.assertNotIn('vd', results[0])

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

    def test_detail(self):
        self.uplace.save()
        response = self.client.get('/uplaces/%s/' % self.uplace.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertIn('userPost', result)
        self.assertIn('placePost', result)
        self.assertNotIn('id', result)
        response = self.client.get('/uplaces/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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

        name1 = ShortText(content='능라'); name1.save()
        posDesc1 = ShortText(content='운중동버스차고지 근처'); posDesc1.save()
        addr11 = ShortText(content='경기도 성남시 분당구 운중동 883-3'); addr11.save()
        addr12 = ShortText(content='경기도 성남시 분당구 산운로32번길 12'); addr12.save()
        note11 = ShortText(content='분당 냉면 최고'); note11.save()
        note12 = ShortText(content='을밀대가 좀 더 낫나? ㅋ'); note12.save()
        note13 = ShortText(content='평양냉면'); note13.save()
        imgNote1 = ShortText(content='냉면 사진'); imgNote1.save()
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img2_content = 'http://blogpfthumb.phinf.naver.net/20100110_16/mardukas_1263055491560_VI01Ic_JPG/DSCN1968.JPG'
        img3_content = 'http://mblogthumb1.phinf.naver.net/20160302_36/mardukas_14569226823176xNHG_JPEG/DSC07314.JPG'
        img1 = Image(content=img1_content); img1.save()
        img2 = Image(content=img2_content); img2.save()
        img3 = Image(content=img3_content); img3.save()
        url11 = Url(content='http://maukistudio.com/'); url11.save()
        url12 = Url(content='http://maukistudio.com/2/'); url12.save()
        url13 = Url(content='http://maukistudio.com/3/'); url13.save()
        lp11 = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square'); lp11.save()
        lp12 = LegacyPlace(content='http://map.naver.com/local/siteview.nhn?code=21149144'); lp12.save()
        lp13 = LegacyPlace(content='ChIJrTLr-GyuEmsRBfy61i59si0.google'); lp13.save()
        phone1 = PhoneNumber(content='010-5597-9245'); phone1.save()

        json_full = '''
            {
                "uplace_uuid": "%s",
                "lonLat": {"lon": %f, "lat": %f, "timestamp": null},
                "name": {"uuid": "%s", "content": "%s", "timestamp": null},
                "posDesc": {"uuid": "%s", "content": "%s", "timestamp": null},
                "phone": {"uuid": "%s", "content": "%s", "timestamp": null},
                "addrs": [
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null}
                ],
                "notes": [
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null}
                ],
                "images": [
                    {"uuid": "%s", "content": "%s", "timestamp": null, "summary": "%s",
                        "note": {"uuid": "%s", "content": "%s", "timestamp": null}},
                    {"uuid": "%s", "content": "%s", "timestamp": null, "summary": "%s", "note": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null, "summary": "%s", "note": null}
                ],
                "urls": [
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null}
                ],
                "lps": [
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null}
                ]
            }
        ''' % (self.uplace.uuid, point1.x, point1.y,
               name1.uuid, name1.content, posDesc1.uuid, posDesc1.content, phone1.uuid, phone1.content,
               addr11.uuid, addr11.content, addr12.uuid, addr12.content,
               note11.uuid, note11.content, note12.uuid, note12.content, note13.uuid, note13.content,
               img1.uuid, img1.content, img1.url_summarized, imgNote1.uuid, imgNote1.content,
               img2.uuid, img2.content, img2.url_summarized, img3.uuid, img3.content, img3.url_summarized,
               url11.uuid, url11.content, url12.uuid, url12.content, url13.uuid, url13.content,
               lp11.uuid, lp11.content, lp12.uuid, lp12.content, lp13.uuid, lp13.content,)
        want = Post(json_full)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_full)); sleep(0.001)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)

        self.assertEqual(want.isSubsetOf(self.uplace.userPost), True)
        want.json['uplace_uuid'] = None
        self.assertEqual(want.isSubsetOf(self.uplace.placePost), True)
        self.assertEqual(self.uplace.userPost.isSubsetOf(want), False)
        self.assertEqual(self.uplace.placePost.isSubsetOf(want), False)

        result = json_loads(response.content)
        self.assertIn('created', result)
        self.assertIn('modified', result)
        t1 = result['modified']
        self.assertIn('place_id', result)
        place_id = result['place_id']
        result_userPost = Post(result['userPost'])
        result_placePost = Post(result['placePost'])
        self.assertDictEqual(result_userPost.json, self.uplace.userPost.json)
        self.assertDictEqual(result_placePost.json, self.uplace.placePost.json)

        # 한번 더...
        self.uplace.clearCache()
        response = self.client.post('/uplaces/', dict(add=json_full))
        self.uplace.clearCache()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)

        self.assertEqual(want.isSubsetOf(self.uplace.userPost), True)
        self.assertEqual(want.isSubsetOf(self.uplace.placePost), True)
        self.assertEqual(self.uplace.userPost.isSubsetOf(want), False)
        self.assertEqual(self.uplace.placePost.isSubsetOf(want), False)

        result = json_loads(response.content)
        self.assertIn('created', result)
        self.assertIn('modified', result)
        t2 = result['modified']
        result_userPost = Post(result['userPost'])
        result_placePost = Post(result['placePost'])

        self.assertDictEqual(result_userPost.json, self.uplace.userPost.json)
        self.assertDictEqual(result_placePost.json, self.uplace.placePost.json)

        self.assertGreater(t2, t1)
        self.assertAlmostEqual(t2, t1, delta=1000)

        # 내장소 목록
        dummy_place = Place(); dummy_place.save()
        self.uplace.clearCache()
        response = self.client.get('/uplaces/?ru=myself')
        self.uplace.clearCache()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        result_userPost = Post(results[0]['userPost'])
        result_placePost = Post(results[0]['placePost'])
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)
        self.assertDictEqual(result_userPost.json, self.uplace.userPost.json)
        self.assertDictEqual(result_placePost.json, self.uplace.placePost.json)

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
                "addrs": [{"uuid": null, "content": "%s"}, {"uuid": null, "content": "%s"}]
            }
        ''' % (point1.x, point1.y, img1.uuid, addr1_content, addr2_content,)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=json_add, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)

        self.uplace = UserPlace.objects.first()
        want = Post(json_add)
        self.assertEqual(want.isSubsetOf(self.uplace.userPost), True)
        self.assertEqual(self.uplace.placePost, None)
        self.assertEqual(self.uplace.userPost.isSubsetOf(want), False)

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
        note11 = ShortText(content='분당 냉면 최고'); note11.save()
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
        want = Post(json_add)
        self.assertEqual(want.isSubsetOf(self.uplace.userPost), True)
        self.assertEqual(self.uplace.placePost, None)
        self.assertEqual(self.uplace.userPost.isSubsetOf(want), False)

    def test_create_case3_only_url(self):
        url1 = Url(content='http://maukistudio.com/'); url1.save()

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
        want = Post(json_add)
        self.assertEqual(want.isSubsetOf(self.uplace.userPost), True)
        self.assertEqual(self.uplace.placePost, None)
        self.assertEqual(self.uplace.userPost.isSubsetOf(want), False)

    def test_create_case4_only_url_and_note(self):
        note11 = ShortText(content='분당 냉면 최고'); note11.save()
        url1 = Url(content='http://maukistudio.com/'); url1.save()

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
        want = Post(json_add)
        self.assertEqual(want.isSubsetOf(self.uplace.userPost), True)
        self.assertEqual(self.uplace.placePost, None)
        self.assertEqual(self.uplace.userPost.isSubsetOf(want), False)

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
        url11_content='http://maukistudio.com/'
        url12_content='http://maukistudio.com/2/'
        url13_content='http://maukistudio.com/3/'
        lp1 = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square'); lp1.save()

        json_add = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": null, "content": "%s"},
                "posDesc": {"uuid": null, "content": "%s"},
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
               name1_content, addr1_content,
               note11_content, note12_content, note13_content,
               img1.uuid, imgNote1_content, img2.uuid, img3.uuid,
               url11_content, url12_content, url13_content,
               lp1.content,)
        want = Post(json_add)

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        self.assertEqual(self.uplace.place, None)
        response = self.client.post('/uplaces/', dict(add=json_add, uplace_uuid=self.uplace.uuid,))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 2)

        self.uplace = UserPlace.objects.first()
        self.assertEqual(want.isSubsetOf(self.uplace.userPost), True)
        self.assertEqual(self.uplace.userPost.isSubsetOf(want), False)
        self.assertNotEqual(self.uplace.place, None)
        self.assertNotEqual(self.uplace.place, self.place)
        self.assertEqual(want.isSubsetOf(self.uplace.placePost), True)
        self.assertEqual(self.uplace.placePost.isSubsetOf(want), False)

    def test_create_by_naver_map_url(self):
        self.uplace.place = self.place
        self.uplace.save()
        url = Url()
        test_data = 'http://map.naver.com/local/siteview.nhn?code=21149144'
        url.content = test_data
        url.save()
        url.summarize()
        want = url.content_summarized

        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)
        response = self.client.post('/uplaces/', dict(add=want.json_str, uplace_uuid=self.uplace.uuid))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserPlace.objects.count(), 1)
        self.assertEqual(Place.objects.count(), 1)

        self.assertEqual(want.isSubsetOf(self.uplace.userPost), True)
        self.assertEqual(self.uplace.userPost.isSubsetOf(want), False)
        self.assertEqual(want.isSubsetOf(self.uplace.placePost), True)
        self.assertEqual(self.uplace.placePost.isSubsetOf(want), False)

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

        result = json_loads(response.content)['userPost']
        self.assertNotEqual(result['urls'][0], None)
        self.assertNotEqual(result['lonLat'], None)
        self.assertNotEqual(result['name'], None)
        self.assertNotEqual(result['phone'], None)
        self.assertNotEqual(result['addrs'][0], None)
        self.assertNotEqual(result['lps'][0], None)
