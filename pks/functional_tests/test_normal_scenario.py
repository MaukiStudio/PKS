#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from rest_framework import status

from base.tests import APITestBase
from account import models


class FirstScenarioTest(APITestBase):

    def test_first_scenario(self):
        # 자동 회원 가입
        response = self.client.post('/users/register/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 유저 로그인 by 토큰
        auth_user_token = json.loads(response.content)['auth_user_token']   # post 와는 다른, 최대한 안전한 storage 에 저장
        self.assertNotLogin()
        response = self.client.post('/users/login/', dict(auth_user_token=auth_user_token))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertLogin()

        # VD 등록
        response = self.client.post('/vds/register/',
                                dict(email='gulby@maukistudio.com',     # required
                                     deviceTypeName='LG-F460L',         # optional
                                     deviceName='ed750c68-ecd1-11e5-b311-382c4a6424bd'))    # optional
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vd = models.VD.objects.first()

        # VD 로그인 by 토큰
        auth_vd_token = json.loads(response.content)['auth_vd_token']       # post 와 같은 storage 에 저장해도 무방
        self.assertVdNotLogin()
        response = self.client.post('/vds/login/', dict(auth_vd_token=auth_vd_token))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertVdLogin()
        auth_vd_token = json.loads(response.content)['auth_vd_token']       # 로그인할 때마다 auth_vd_token 은 갱신

        # VD 정보 조회
        # 해당 VirtualDevice 에서 생성한 PlaceContent 정보로 구성된 PlacePost 정보 조회
        # 현재까지는 저장한 것이 하나도 없으므로 조회 결과는 없음
        response = self.client.get('/vds/mine/posts/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(0, len(json.loads(response.content)))

        # RealUser(VD.realOwner) 에 매핑된 VD 목록 조회
        # 현재 로그인한 VD 는 빼고 조회됨
        response = self.client.get('/rus/mine/vds/')

        # 이메일 인증이 되지 않은 경우 404 Not Found 가 발생
        # TODO : 현재는 임시로 VD 등록 시 이메일 인증도 완료된 걸로 처리되어 있음
        # TODO : 따라서 404 가 발생하지 않음. 추후 주석 제거
        #self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 앱 종료
        self.logout()

        # 이메일 인증
        # TODO : 현재는 임시로 VD 등록 시 이메일 인증도 완료된 걸로 처리되어 있음
        # TODO : 나중에 이메일을 읽어 인증 링크를 클릭하도록 구현 수정

        # 앱 재시작

        # 유저 로그인 by 토큰
        self.assertNotLogin()
        response = self.client.post('/users/login/', dict(auth_user_token=auth_user_token))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertLogin()

        # VD 로그인 by 토큰
        self.assertVdNotLogin()
        response = self.client.post('/vds/login/', dict(auth_vd_token=auth_vd_token))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertVdLogin()

        # RealUser(VD.realOwner) 에 매핑된 VD 목록 조회
        response = self.client.get('/rus/mine/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 하나도 없음을 확인 : 자기자신은 포함되지 않으므로 하나도 없음
        vds = json.loads(response.content)
        self.assertEqual(len(vds), 0)

        # 새로운 단말기에서 같은 RealUser 로...
        self.logout()
        response = self.client.post('/users/register/')
        auth_user_token_other = json.loads(response.content)['auth_user_token']
        response = self.client.post('/users/login/', dict(auth_user_token=auth_user_token_other))
        response = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        auth_vd_token_other = json.loads(response.content)['auth_vd_token']
        response = self.client.post('/vds/login/', dict(auth_vd_token=auth_vd_token_other))
        self.assertLogin()
        self.assertVdLogin()

        # RealUser(VD.realOwner) 에 매핑된 VD 목록 조회
        response = self.client.get('/rus/mine/vds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 앞서 생성되어 있던 VD 1개가 존재함을 확인
        vds = json.loads(response.content)
        self.assertEqual(len(vds), 1)
        self.assertEqual(vd.id, vds[0]['id'])





        # 장소 저장
        self.fail('장소 저장 로직 구현')

