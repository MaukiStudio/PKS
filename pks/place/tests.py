#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads, dumps as json_dumps
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry

from base.tests import APITestBase
from place import models
from image.models import Image
from content.models import ShortText, LegacyPlace
from url.models import Url
from account.models import VD


class PlaceViewSetTest(APITestBase):

    def setUp(self):
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.place = models.Place(); self.place.save()

    def test_list(self):
        response = self.client.get('/places/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 1)
        self.assertIn('placePost', result['results'][0])

    def test_detail(self):
        response = self.client.get('/places/%s/' % self.place.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertIn('id', result)
        self.assertNotIn('vds', result)
        self.assertIn('placePost', result)
        response = self.client.get('/places/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PlaceContentViewSetTest(APITestBase):

    def setUp(self):
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


class UserPostViewSetTest(APITestBase):

    def setUp(self):
        response = self.client.post('/users/register/')
        self.auth_user_token = json_loads(response.content)['auth_user_token']
        self.client.post('/users/login/', {'auth_user_token': self.auth_user_token})
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.auth_vd_token = json_loads(response.content)['auth_vd_token']
        self.client.post('/vds/login/', {'auth_vd_token': self.auth_vd_token})
        self.place = models.Place(); self.place.save()
        self.vd = VD.objects.first()
        self.post = models.UserPost(vd=self.vd, place=self.place)

    def test_list(self):
        self.post.save()
        response = self.client.get('/uposts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 1)
        self.assertIn('userPost', result['results'][0])
        self.assertIn('placePost', result['results'][0])
        self.assertNotIn('id', result['results'][0])

    def test_detail(self):
        self.post.save()
        response = self.client.get('/uposts/%s/' % self.post.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(type(result), dict)
        self.assertIn('userPost', result)
        self.assertIn('placePost', result)
        self.assertNotIn('id', result)
        response = self.client.get('/uposts/null/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_full(self):
        point1 = GEOSGeometry('POINT(127 37)')
        name1 = ShortText(content='능라'); name1.save()
        addr1 = ShortText(content='경기도 성남시 분당구 운중동 883-3'); addr1.save()
        note11 = ShortText(content='분당 냉면 최고'); note11.save()
        note12 = ShortText(content='을밀대가 좀 더 낫나? ㅋ'); note12.save()
        note13 = ShortText(content='평양냉면'); note13.save()
        imgNote1 = ShortText(content='냉면 사진'); imgNote1.save()
        img1 = Image(file=self.uploadImage('test.jpg')); img1.save()
        img2 = Image(file=self.uploadImage('no_exif_test.jpg')); img2.save()
        img3 = Image(file=self.uploadImage('test_480.jpg')); img3.save()
        url11 = Url(content='http://maukistudio.com/'); url11.save()
        url12 = Url(content='http://maukistudio.com/2/'); url12.save()
        url13 = Url(content='http://maukistudio.com/3/'); url13.save()
        lp11 = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square'); lp11.save()
        lp12 = LegacyPlace(content='http://map.naver.com/local/siteview.nhn?code=21149144'); lp12.save()
        lp13 = LegacyPlace(content='ChIJrTLr-GyuEmsRBfy61i59si0.google'); lp13.save()

        json_add = '''
            {
                "place_id": %d,
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": "%s", "content": "%s"},
                "posDesc": {"uuid": "%s", "content": "%s"},
                "notes": [
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"}
                ],
                "images": [
                    {"uuid": "%s", "content": null, "note": {"uuid": "%s", "content": "%s"}},
                    {"uuid": "%s", "content": null, "note": null},
                    {"uuid": "%s", "content": null, "note": null}
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
        ''' % (self.place.id, point1.x, point1.y,
               name1.uuid, name1.content, addr1.uuid, addr1.content,
               note11.uuid, note11.content, note12.uuid, note12.content, note13.uuid, note13.content,
               img1.uuid, imgNote1.uuid, imgNote1.content, img2.uuid, img3.uuid,
               url11.uuid, url11.content, url12.uuid, url12.content, url13.uuid, url13.content,
               lp11.uuid, lp11.content, lp12.uuid, lp12.content, lp13.uuid, lp13.content,)
        want = json_loads(json_add)

        self.assertEqual(models.UserPost.objects.count(), 0)
        self.assertEqual(models.Place.objects.count(), 1)
        response = self.client.post('/uposts/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.UserPost.objects.count(), 1)
        self.assertEqual(models.Place.objects.count(), 1)
        self.assertDictEqual(self.post.userPost, want)
        self.assertDictEqual(self.post.placePost, want)
        result = json_loads(response.content)
        self.assertDictEqual(result['userPost'], want)
        self.assertDictEqual(result['placePost'], want)

        dummy_place = models.Place(); dummy_place.save()
        response = self.client.get('/uposts/?ru=myself')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)
        self.assertDictEqual(results[0]['userPost'], want)
        self.assertDictEqual(results[0]['placePost'], want)


    def test_create_case1_current_pos_only_with_photo(self):
        point1 = GEOSGeometry('POINT(127 37)')
        img1 = Image(file=self.uploadImage('test.jpg')); img1.save()

        json_add = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "images": [{"uuid": "%s", "content": null, "note": null}]
            }
        ''' % (point1.x, point1.y, img1.uuid,)

        self.assertEqual(models.UserPost.objects.count(), 0)
        self.assertEqual(models.Place.objects.count(), 1)
        response = self.client.post('/uposts/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.UserPost.objects.count(), 1)
        self.assertEqual(models.Place.objects.count(), 2)

        self.post = models.UserPost.objects.first()
        json_want = '''
            {
                "place_id": %d,
                "lonLat": {"lon": %f, "lat": %f},
                "name": null,
                "posDesc": null,
                "notes": [],
                "images": [{"uuid": "%s", "content": null, "note": null}],
                "urls": [],
                "lps": []
            }
        ''' % (self.post.userPost['place_id'], point1.x, point1.y, img1.uuid,)
        want = json_loads(json_want)
        self.assertDictEqual(self.post.userPost, want)
        self.assertDictEqual(self.post.placePost, want)

    def test_create_case2_current_pos_with_note_photo(self):
        point1 = GEOSGeometry('POINT(127 37)')
        note11 = ShortText(content='분당 냉면 최고'); note11.save()
        img1 = Image(file=self.uploadImage('test.jpg')); img1.save()

        json_add = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "notes": [{"uuid": "%s", "content": null}],
                "images": [{"uuid": "%s", "content": null, "note": null}]
            }
        ''' % (point1.x, point1.y, note11.uuid, img1.uuid,)

        self.assertEqual(models.UserPost.objects.count(), 0)
        self.assertEqual(models.Place.objects.count(), 1)
        response = self.client.post('/uposts/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.UserPost.objects.count(), 1)
        self.assertEqual(models.Place.objects.count(), 2)

        self.post = models.UserPost.objects.first()
        json_want = '''
            {
                "place_id": %d,
                "lonLat": {"lon": %f, "lat": %f},
                "name": null,
                "posDesc": null,
                "notes": [{"uuid": "%s", "content": "%s"}],
                "images": [{"uuid": "%s", "content": null, "note": null}],
                "urls": [],
                "lps": []
            }
        ''' % (self.post.userPost['place_id'], point1.x, point1.y, note11.uuid, note11.content, img1.uuid,)
        want = json_loads(json_want)
        self.assertDictEqual(self.post.userPost, want)
        self.assertDictEqual(self.post.placePost, want)

    def test_create_case3_only_url(self):
        url1 = Url(content='http://maukistudio.com/'); url1.save()

        json_add = '''
            {
                "urls": [{"uuid": "%s", "content": null}]
            }
        ''' % (url1.uuid,)

        self.assertEqual(models.UserPost.objects.count(), 0)
        self.assertEqual(models.Place.objects.count(), 1)
        response = self.client.post('/uposts/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.UserPost.objects.count(), 1)
        self.assertEqual(models.Place.objects.count(), 2)

        self.post = models.UserPost.objects.first()
        json_want = '''
            {
                "place_id": %d,
                "lonLat": null,
                "name": null,
                "posDesc": null,
                "notes": [],
                "images": [],
                "urls": [{"uuid": "%s", "content": "%s"}],
                "lps": []
            }
        ''' % (self.post.userPost['place_id'], url1.uuid, url1.content,)
        want = json_loads(json_want)
        self.assertDictEqual(self.post.userPost, want)
        self.assertDictEqual(self.post.placePost, want)

    def test_create_case4_only_url_and_note(self):
        note11 = ShortText(content='분당 냉면 최고'); note11.save()
        url1 = Url(content='http://maukistudio.com/'); url1.save()

        json_add = '''
            {
                "notes": [{"uuid": "%s", "content": null}],
                "urls": [{"uuid": "%s", "content": null}]
            }
        ''' % (note11.uuid, url1.uuid,)

        self.assertEqual(models.UserPost.objects.count(), 0)
        self.assertEqual(models.Place.objects.count(), 1)
        response = self.client.post('/uposts/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.UserPost.objects.count(), 1)
        self.assertEqual(models.Place.objects.count(), 2)

        self.post = models.UserPost.objects.first()
        json_want = '''
            {
                "place_id": %d,
                "lonLat": null,
                "name": null,
                "posDesc": null,
                "notes": [{"uuid": "%s", "content": "%s"}],
                "images": [],
                "urls": [{"uuid": "%s", "content": "%s"}],
                "lps": []
            }
        ''' % (self.post.userPost['place_id'], note11.uuid, note11.content, url1.uuid, url1.content,)
        want = json_loads(json_want)
        self.assertDictEqual(self.post.userPost, want)
        self.assertDictEqual(self.post.placePost, want)

    def test_create_case5_no_info(self):
        json_add = '''
            {
            }
        '''

        self.assertEqual(models.UserPost.objects.count(), 0)
        self.assertEqual(models.Place.objects.count(), 1)
        response = self.client.post('/uposts/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(models.UserPost.objects.count(), 0)
        self.assertEqual(models.Place.objects.count(), 1)

    def test_create_full_with_no_uuid_except_image(self):
        point1 = GEOSGeometry('POINT(127 37)')
        name1_content = '능라'
        addr1_content='경기도 성남시 분당구 운중동 883-3'
        note11_content='분당 냉면 최고'
        note12_content='을밀대가 좀 더 낫나? ㅋ'
        note13_content='평양냉면'
        imgNote1_content='냉면 사진'
        img1 = Image(file=self.uploadImage('test.jpg')); img1.save()
        img2 = Image(file=self.uploadImage('no_exif_test.jpg')); img2.save()
        img3 = Image(file=self.uploadImage('test_480.jpg')); img3.save()
        url11_content='http://maukistudio.com/'
        url12_content='http://maukistudio.com/2/'
        url13_content='http://maukistudio.com/3/'
        lp1 = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square'); lp1.save()

        json_add = '''
            {
                "place_id": %d,
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
        ''' % (self.place.id, point1.x, point1.y,
               name1_content, addr1_content,
               note11_content, note12_content, note13_content,
               img1.uuid, imgNote1_content, img2.uuid, img3.uuid,
               url11_content, url12_content, url13_content,
               lp1.content,)
        want = json_loads(json_add)

        self.assertEqual(models.UserPost.objects.count(), 0)
        self.assertEqual(models.Place.objects.count(), 1)
        response = self.client.post('/uposts/', dict(add=json_add))

        # TODO : 향후 json 안에 null 인 uuid 를 채우는 수정 필요
        want = self.post.userPost
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.UserPost.objects.count(), 1)
        self.assertEqual(models.Place.objects.count(), 1)
        self.assertDictEqual(self.post.userPost, want)
        self.assertDictEqual(self.post.placePost, want)
        result = json_loads(response.content)
        self.assertDictEqual(result['userPost'], want)
        self.assertDictEqual(result['placePost'], want)

        dummy_place = models.Place(); dummy_place.save()
        response = self.client.get('/uposts/?ru=myself')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)
        self.assertDictEqual(results[0]['userPost'], want)
        self.assertDictEqual(results[0]['placePost'], want)