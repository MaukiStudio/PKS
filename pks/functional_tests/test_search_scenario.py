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
                "addrs": [{"content": "경기도 성남시 분당구 판교로 256번길 25"}, {"content": "경기도 성남시 분당구 삼평동 631"}],
                "urls": [{"content": "http://map.naver.com/local/siteview.nhn?code=21149144"}]
            }
        '''
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_uplaces_only_my_places(self):

        # 특정 유저 장소 조회 : 현재는 내 장소 목록 조회만 구현됨
        # 이메일 인증이 되지 않은 시점에서도 ru=myself 는 동작함 (이땐 vd=myself 와 동일)
        # ru 파라메터가 생략되면 디폴트로 myself 이며, ru 에 다른 유저의 값을 할당하는 것은 미구현 상태 (영원히 구현 안할지도;;;)

        # limit : 목록 조회시 넘어가는 결과의 개수. default=100
        # offset : 목록 조회를 시작하는 위치 (0에서 시작) (페이지 번호와는 다름). default=0
        # 10개씩 보여줄 때 20페이지는 limit=10&offset=10*(20-1)=190 임
        # 이러한 페이징 인터페이스는 /places/ API 에도 동일하게 적용됨

        response = self.client.get('/uplaces/?ru=myself&limit=1000&offset=0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertIn('userPost', results[0])
        self.assertIn('placePost', results[0])

    def test_places_all_places(self):

        # 장소 목록 조회
        # TODO : 위치기반 뿐만 아니라 각종 다양한 검색 조건을 지원 (개인화 추천 알고리즘 포함)

        # 전체 장소 목록 조회
        # 내 장소가 아닌 장소는 userPost.place_id 빼고 모두 null 임
        response = self.client.get('/places/?lon=127.1037430&lat=37.3997320&r=1000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertNotIn('userPost', results[0])
        self.assertIn('placePost', results[0])
