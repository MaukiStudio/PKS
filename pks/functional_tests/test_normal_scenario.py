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
        auth_user_token = json.loads(res1.content)['auth_user_token']   # post 와는 다른, 최대한 안전한 storage 에 저장
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
        self.assertVdNotLogin()
        res5 = self.client.post('/vds/login/', dict(auth_vd_token=auth_vd_token))
        self.assertEqual(res5.status_code, status.HTTP_302_FOUND)
        self.assertVdLogin()
        auth_vd_token = json.loads(res5.content)['auth_vd_token']       # 로그인할 때마다 auth_vd_token 은 갱신

        # RealUser(VD.realOwner) 에 매핑된 VD 목록 조회
        res6 = self.client.get('/rus/mine/')

        # 이메일 인증이 되지 않은 경우 404 Not Found 가 발생
        # TODO : 현재는 임시로 VD 등록 시 이메일 인증도 완료된 걸로 처리되어 있음
        # TODO : 따라서 404 가 발생하지 않음. 추후 주석 제거
        self.assertEqual(res6.status_code, status.HTTP_404_NOT_FOUND)

        # 앱 종료
        self.logout()

        # 이메일 인증
        # TODO : 현재는 임시로 VD 등록 시 이메일 인증도 완료된 걸로 처리되어 있음
        # TODO : 나중에 이메일을 읽어 인증 링크를 클릭하도록 구현 수정

        # 앱 재시작

        # 유저 로그인 by 토큰
        self.assertNotLogin()
        res7 = self.client.post('/users/login/', dict(auth_user_token=auth_user_token))
        self.assertEqual(res7.status_code, status.HTTP_302_FOUND)
        self.assertLogin()

        # VD 로그인 by 토큰
        self.assertVdNotLogin()
        res8 = self.client.post('/vds/login/', dict(auth_vd_token=auth_vd_token))
        self.assertEqual(res8.status_code, status.HTTP_302_FOUND)
        self.assertVdLogin()

        # VD 정보 조회
        res9 = self.client.get('/vds/mine/')
        self.assertEqual(res6.status_code, status.HTTP_200_OK)

        # VD.realOwner 정보가 세팅되어 있음을 확인
        realOwner = json.loads(res9.content)['realOwner']
        self.assertIsNotNone(realOwner)

        # realOwner 의 VD 목록 조회
        res10 = self.client.get('/rus/%s/' % realOwner)
        self.assertEqual(res10.status_code, status.HTTP_200_OK)

        # res10 에서 VD 목록이 있는지 확인
        vds = json.loads(res10.content)['vds']
        #self.assertListEqual(vds, [])

        # 장소 저장
        self.fail('장소 저장 로직 구현')


