#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import FunctionalTestAfterLoginBase


class SimpleSearchScenarioTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        # User/VD 로그인
        super(SimpleSearchScenarioTest, self).setUp()

        # 현재 위치 저장
        json_add = '''
            {
                "lonLat": {"lon": 127.1037430, "lat": 37.3997320},
                "images": [{"content": "http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg"}],
                "addr1": {"content": "경기도 성남시 분당구 판교로 256번길 25"},
                "addr2": {"content": "경기도 성남시 분당구 삼평동 631"},
                "addr3": {"content": "경기도 성남시 분당구 삼평동"},
                "urls": [{"content": "http://place.map.daum.net/15738374"}]
            }
        '''
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_uplaces_only_my_places(self):
        # 내 장소 목록 조회
        # ru : myself 만 허용됨 (default=myself)
        # limit : 목록 조회시 넘어가는 결과의 개수. default=100
        # offset : 목록 조회를 시작하는 위치 (0에서 시작) (페이지 번호와는 다름). default=0
        # 10개씩 보여줄 때 20페이지는 limit=10&offset=10*(20-1)=190 임
        # 이러한 페이징 인터페이스는 /places/ API 에도 동일하게 적용됨
        # userPost 와 placePost 모두 조회됨

        # 지원 order_by : 'distance_from_origin', '-distance_from_origin', 'modified', '-modified'
        # 장소화 여부 검색 - placed : True, False

        response = self.client.get('/uplaces/?lon=127.1037430&lat=37.3997320&r=0&limit=1000&offset=0&order_by=-distance_from_origin&placed=True')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)
        self.assertIn('userPost', results[0])
        self.assertIn('placePost', results[0])
        self.assertIn('uplace_uuid', results[0])
        self.assertIn('place_id', results[0])

    def test_places_all_places(self):
        # 전체 장소 목록 조회
        # placePost 만 조회됨. 내 장소의 userPost 는 /uplaces/ 로 얻어오면 됨 (동일 장소 여부는 place_id 로)
        # 하기 샘플의 lon/lat/r 인터페이스는 /uplaces/ 에도 동일하게 적용됨
        response = self.client.get('/places/?lon=127.1037430&lat=37.3997320&r=10000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)
        self.assertNotIn('userPost', results[0])
        self.assertIn('placePost', results[0])
        self.assertIn('place_id', results[0])

    def test_uplaces_delete(self):
        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)
        self.assertIn('uplace_uuid', results[0])
        uplace_uuid = results[0]['uplace_uuid']

        # 삭제
        id = uplace_uuid.split('.')[0]  # dot(.) 부터 뒤로 짤라 없앤 32글자로 접근 (DRF Framework 어딘가에서 . 을 잡아 먹음 ㅠ_ㅜ)
        response = self.client.delete('/uplaces/%s/' % id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 0)

    def test_uplaces_regions(self):
        response = self.client.get('/uplaces/regions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)
        self.assertEqual(len(results), 1)
        self.assertIn('lonLat', results[0])
        self.assertIn('count', results[0])
        self.assertIn('radius', results[0])
