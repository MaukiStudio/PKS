#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from functional_tests.ftbase import FunctionalTestAfterLoginBase


class PostScenarioTest(FunctionalTestAfterLoginBase):

    def test_post_by_current_pos(self):
        # 사전에 (앱 실행 직후) 높은 정확도의 GPS 정보 조회 : GPS 정확도를 높이기 위함
        lon, lat = self.get_gps_info()

        # 현재 위치 저장 누르자마자 높은 정확도의 GPS 정보 조회 : GPS 정확도를 높이기 위함
        lon, lat = self.get_gps_info()

        photo = self.take_picture()

        # 작은쪽이 640 을 넘지 않도록 하는 ratio 보존 사이즈 줄이기
        # EXIF 정보가 있다면 보존 (Orientation 정보는 상황에 따라 바뀔 수도...)
        resized = self.resize_image(photo)

        # 최종적으로 사용할 GPS 정보
        lon, lat = self.get_gps_info()

        # 주소값 조회

        # 사진찍은 직후에 서버에 등록 : 현재 위치 저장 완료 하기 전에 미리 진행
        with open(resized) as f:
            response = self.client.post('/imgs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        img_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(img_uuid)

        # 노트 등록 : 가능한한 빨리 미리 등록
        response = self.client.post('/stxts/', dict(content='장소 노트'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        note_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(note_uuid)

        # 드디어! 현재 위치 저장
        # notes 가 list type 이지만 post create 시엔 1개만 가능
        # image 는 여러개가 가능하지만, 일단 place 를 만든 다음에 추가하는 식으로 UI를 짜는게 좋지 않을까...
        # image 가 여러개인 경우, list 상의 첫번째 사진이 중요. 유저가 방금 찍은 사진이 되도록...
        json_add = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "notes": [{"uuid": "%s", "content": null}],
                "images": [{"uuid": "%s", "content": null, "note": null}]
            }
        ''' % (lon, lat, note_uuid, img_uuid,)
        response = self.client.post('/uposts/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 결과값에서 userPost, placePost 조회
        result = json_loads(response.content)
        userPost = result['userPost']
        placePost = result['placePost']



