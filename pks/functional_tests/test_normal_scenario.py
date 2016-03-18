#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from rest_framework import status

from base.tests import APITestBase


class FirstScenarioTest(APITestBase):

    def test_first_scenario(self):
        # 자동 회원 가입
        res1 = self.client.post('/users/register/')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # 유저 로그인 by 토큰
        auth_user_token = json.loads(res1.content)['auth_user_token']   # post 와는 다른 storage 에 저장
        self.assertNotLogin()
        res2 = self.client.post('/users/login/', dict(auth_user_token=auth_user_token))
        self.assertEqual(res2.status_code, status.HTTP_302_FOUND)
        self.assertLogin()

        # VD 등록
        res3 = self.client.post('/vds/register/',
                                dict(email='gulby@maukistudio.com',     # required
                                     deviceTypeName='LG-F460L',         # optional
                                     deviceName='ed750c68-ecd1-11e5-b311-382c4a6424bd'))    # optional
        self.assertEqual(res3.status_code, status.HTTP_201_CREATED)

        # VD 로그인 by 토큰
        auth_vd_token = json.loads(res3.content)['auth_vd_token']       # post 와 같은 storage 에 저장해도 무방
        res5 = self.client.post('/vds/login/', dict(auth_vd_token=auth_vd_token))
        self.assertEqual(res5.status_code, status.HTTP_302_FOUND)

        # 해당 RealUser 의 모든 VD 목록 조회
        # 이때는 자기자신을 제외하고는 아무것도 없어야 함

        # 앱 종료

        # 이메일 인증 : 현재는 임시로 VD 등록 시 이메일 인증도 완료된 걸로 처리되어 있음

        # 앱 재시작

        # 유저 로그인 by 토큰
        res2 = self.client.post('/users/login/', dict(auth_user_token=auth_user_token))
        self.assertEqual(res2.status_code, status.HTTP_302_FOUND)
        self.assertLogin()

        # VD 로그인 by 토큰

        # 장소 저장
        self.fail('장소 저장 로직 구현')


