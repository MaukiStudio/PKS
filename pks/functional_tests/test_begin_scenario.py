#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import FunctionalTestBase, FunctionalTestAfterLoginBase


class RegisterScenarioTest(FunctionalTestBase):

    def test_register(self):
        # Register User (only for auth)
        response = self.client.post('/users/register/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.secureStorage['auth_user_token'] = json_loads(response.content)['auth_user_token']

        # User Login by Token
        self.assertNotLogin()
        response = self.client.post('/users/login/', dict(auth_user_token=self.secureStorage['auth_user_token']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLogin()

        # Register VD
        email = self.input_from_user()
        country = 'KR'
        language = 'ko'
        timezone = 'KST'
        data = '{"any json": "ok"}'
        response = self.client.post('/vds/register/', dict(email=email, country=country, language=language, timezone=timezone, data=data))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']


class LoginScenarioTest(FunctionalTestBase):

    def setUp(self):
        response = self.client.post('/users/register/')
        self.secureStorage['auth_user_token'] = json_loads(response.content)['auth_user_token']
        response = self.client.post('/users/login/', dict(auth_user_token=self.secureStorage['auth_user_token']))
        email = self.input_from_user()
        response = self.client.post('/vds/register/', dict(email=email,))
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']
        self.logout()

    def test_login(self):

        # User 로그인 by Token
        self.assertNotLogin()
        response = self.client.post('/users/login/', dict(auth_user_token=self.secureStorage['auth_user_token']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLogin()

        # VD 로그인
        self.assertVdNotLogin()
        response = self.client.post('/vds/login/', dict(auth_vd_token=self.normalStorage['auth_vd_token']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertVdLogin()
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']


class StartScenarioTest(FunctionalTestAfterLoginBase):

    def test_places_myself_with_no_place(self):

        # 내 장소 목록 조회 : userPost 와 placePost 가 한꺼번에 넘어옴
        # 이메일 인증이 되지 않은 시점에서도 ru=myself 는 동작하며, vd=myself 와 동일
        # limit : 목록 조회시 넘어가는 결과의 개수. default=100
        # offset : 목록 조회를 시작하는 위치 (0에서 시작) (페이지 번호와는 다름). default=0
        # 10개씩 보여줄 때 20페이지는 limit=10&offset=10*(20-1)=190 임
        response = self.client.get('/uplaces/?ru=myself&limit=1000&offset=0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(results, list())


    def test_places_pos_with_no_place(self):

        # 위치 기반 장소 목록 조회
        # TODO : 아직 구현되어 있지 않음. 구현해야 함. 일단 /uplaces/?ru=myself 만 사용할 것
        # TODO : 위치기반 뿐만 아니라 각종 다양한 검색 조건을 지원 (개인화 추천 알고리즘 포함)

        # 내장소 목록 조회 : userPost, placePost 둘다 넘어옴
        response = self.client.get('/uplaces/?lon=127.0&lat=37.0&r=1000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(results, list())

        # 전체장소 목록 조회 : publicPost 만 넘어옴
        response = self.client.get('/places/?lon=127.0&lat=37.0&r=1000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(results, list())

