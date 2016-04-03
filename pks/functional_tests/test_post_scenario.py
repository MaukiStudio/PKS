#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from functional_tests.ftbase import FunctionalTestAfterLoginBase


class PostScenarioTest(FunctionalTestAfterLoginBase):

    def test_post_by_current_pos_with_photo(self):
        # 사진찍기 전에 먼저 높은 정확도의 GPS 위치 조회 : GPS 정확도를 높이기 위함
        lon, lat = self.gps_input()

        # 사진찍고 곧바로 서버에 등록 : 현재 위치 저장 완료 하기 전에 미리 진행
        with open('image/samples/test.jpg') as f:
            response = self.client.post('/imgs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        img_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(img_uuid)

        # 노트 등록 : 현재 위치 저장 완료 전에 미리 진행해도 무방
        response = self.client.post('/stxts/', dict(content='장소 노트'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        stxt_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(stxt_uuid)
