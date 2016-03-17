#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from rest_framework import status

from base.tests import APITestBase


class NormalScenarioTest(APITestBase):
    def test_first_by_app(self):
        # 자동 회원 가입
        res1 = self.client.post('/users/register/')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # 유저 로그인 by 토큰
        auth_user_token = json.loads(res1.content)['auth_user_token']
        self.assertNotLogin()
        res2 = self.client.post('/users/login/', dict(auth_user_token=auth_user_token))
        self.assertEqual(res2.status_code, status.HTTP_302_FOUND)
        self.assertLogin()

        # VD 등록
        res3 = self.client.post('/vds/register/', dict(email='gulby@maukistudio.com'))
        self.assertEqual(res3.status_code, status.HTTP_201_CREATED)

        # VD 로그인 by 토큰
        auth_vd_token = json.loads(res3.content)['auth_vd_token']
        res5 = self.client.post('/vds/login/', dict(auth_vd_token=auth_vd_token))
        self.assertEqual(res5.status_code, status.HTTP_302_FOUND)

        # 장소 저장
        self.fail('장소 저장 로직 구현')

