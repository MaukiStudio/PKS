#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import FunctionalTestAfterLoginBase


class PostScenarioTest(FunctionalTestAfterLoginBase):
    '''
        Post Json Schema
            {
                "uplace_uuid": "%s",
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": "%s", "content": "%s"},
                "phone": {"uuid": "%s", "content": "%s"},
                "addr1": {"uuid": "%s", "content": "%s"},
                "addr2": {"uuid": "%s", "content": "%s"},
                "addr3": {"uuid": "%s", "content": "%s"},
                "notes": [
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null},
                    {"uuid": "%s", "content": "%s", "timestamp": null}
                ],
                "images": [
                    {"uuid": "%s", "content": "%s", "timestamp": null, "summary": "%s",
                        "note": {"uuid": "%s", "content": "%s", "timestamp": null}},
                    {"uuid": "%s", "content": "%s", "timestamp": null, "summary": "%s"},
                    {"uuid": "%s", "content": "%s", "timestamp": null, "summary": "%s"}
                ],
                "urls": [
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"}
                ],
                "lps": [
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"}
                ]
            }
    '''

    def test_post_by_current_pos(self):
        #######################################
        # 현재 위치 저장
        #######################################

        # 사전에 (앱 실행 직후) 높은 정확도의 GPS 정보 조회 : GPS 정확도를 높이기 위함
        lon, lat = self.get_gps_info()

        # 사진 찍기
        photo = self.take_picture()

        # 최종적으로 사용할 GPS 정보
        lon, lat = self.get_gps_info()

        # 큰쪽이 1280 을 넘지 않도록 하는 ratio 보존 사이즈 줄이기
        # EXIF 정보가 있다면 보존 (Orientation 정보는 상황에 따라 바뀔 수도...)
        resized = self.resize_image(photo)

        # 사진찍은 직후에 서버에 등록 : 현재 위치 저장 완료 하기 전에 미리 진행
        # 파일 등록
        with open(resized) as f:
            response = self.client.post('/rfs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        file_url = json_loads(response.content)['file']
        first_file_url = file_url

        # 주소값 조회
        addr1_new = '경기도 성남시 분당구 산운로32번길 12'
        addr2_jibun = '경기도 성남시 분당구 운중동 883-3'   # 한국만 존재
        addr3_region = '경기도 성남시 분당구 운중동'

        # 노트 입력 받기
        note = self.input_from_user('장소 노트')

        # 현재 위치 저장
        json_add = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "notes": [{"content": "%s"}],
                "images": [{"content": "%s"}],
                "addr1": {"content": "%s"},
                "addr2" : {"content": "%s"},
                "addr3" : {"content": "%s"}
            }
        ''' % (lon, lat, note, file_url, addr1_new, addr2_jibun, addr3_region,)
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 결과값에서 userPost, placePost 조회
        result = json_loads(response.content)
        userPost = result['userPost']
        placePost = result['placePost']

        # uplace_uuid 조회
        uplace_uuid = result['uplace_uuid']
        self.assertValidUuid(uplace_uuid)

        # placePost == null 이면 장소 정보 수집중... 이라 표시하면 됨
        is_progress = placePost is None
        self.assertEqual(is_progress, True)


        #######################################
        # 사진 추가 with 사진노트
        #######################################
        with open('image/samples/no_exif_test.jpg') as f:
            response = self.client.post('/rfs/', dict(file=f))
        file_url = json_loads(response.content)['file']
        note = self.input_from_user('사진 노트')
        json_add = '''
            {
                "uplace_uuid": "%s",
                "images": [{"content": "%s", "note": {"content": "%s"}}]
            }
        ''' % (uplace_uuid, file_url, note,)
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = json_loads(response.content)
        userPost = result['userPost']
        placePost = result['placePost']
        self.assertEqual(len(userPost['images']), 2)


        #######################################
        # 사진 삭제
        #######################################
        json_remove = '''
            {
                "uplace_uuid": "%s",
                "images": [{"content": "%s"}]
            }
        ''' % (uplace_uuid, first_file_url,)
        response = self.client.post('/uplaces/', dict(remove=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = json_loads(response.content)
        userPost = result['userPost']
        placePost = result['placePost']
        self.assertEqual(len(userPost['images']), 1)


        # Only for server test... (Not interface guide)
        if True:
            response = self.client.get('/uplaces/?ru=myself')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = json_loads(response.content)['results']
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['userPost'], userPost)
            self.assertEqual(results[0]['placePost'], placePost)


    def test_post_by_url(self):

        # URL 입력 받음
        url = self.input_from_user('http://maukistudio.com/')

        # 노트 입력 받기
        note = self.input_from_user('URL 노트')

        # URL 위치 저장
        json_add = '''
            {
                "notes": [{"content": "%s"}],
                "urls": [{"content": "%s"}]
            }
        ''' % (note, url,)
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 결과값에서 userPost, placePost 조회
        result = json_loads(response.content)
        userPost = result['userPost']
        placePost = result['placePost']

        # uplace_uuid 조회
        uplace_uuid = result['uplace_uuid']
        self.assertValidUuid(uplace_uuid)

        # placePost == null 이면 장소 정보 수집중... 이라 표시하면 됨
        is_progress = placePost is None
        self.assertEqual(is_progress, True)


        # Only for server test... (Not interface guide)
        if True:
            response = self.client.get('/uplaces/?ru=myself')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = json_loads(response.content)['results']
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['userPost'], userPost)
            self.assertEqual(results[0]['placePost'], placePost)


    def __skip__test_post_by_FourSquare(self):

        self.fail()
