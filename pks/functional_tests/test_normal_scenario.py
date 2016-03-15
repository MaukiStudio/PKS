#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from django.contrib.sessions.models import Session
from rest_framework.test import APITestCase
from rest_framework import status


class NormalScenarioTest(APITestCase):
    def test_first_by_app(self):
        # 자동 회원 가입
        res1 = self.client.post('/users/register/')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # 토큰 로그인
        auth_user_token = json.loads(res1.content)['auth_user_token']
        self.assertEqual(0, Session.objects.count())
        res2 = self.client.post('/users/login/', {'auth_user_token': auth_user_token})
        self.assertEqual(res2.status_code, status.HTTP_302_FOUND)
        self.assertEqual(1, Session.objects.count())

        # VD 등록
        self.fail('VD 등록 구현')