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
        res2 = self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        self.assertEqual(res2.status_code, status.HTTP_302_FOUND)
        self.assertLogin()

        # VD 등록
        res3 = self.client.post('/vds/register/')
        self.assertEqual(res3.status_code, status.HTTP_201_CREATED)

        # Session 에 VD 세팅 by 토큰
        self.fail()


