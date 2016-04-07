#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from functional_tests.ftbase import FunctionalTestAfterLoginBase


class PostScenarioTest(FunctionalTestAfterLoginBase):
    '''
        Post Json Schema
            {
                "place_id": %d,
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": "%s", "content": "%s"},
                "posDesc": {"uuid": "%s", "content": "%s"},
                "addrs": [
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"}
                ],
                "notes": [
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"}
                ],
                "images": [
                    {"uuid": "%s", "content": "%s", "note": {"uuid": "%s", "content": "%s"}},
                    {"uuid": "%s", "content": "%s", "note": null},
                    {"uuid": "%s", "content": "%s", "note": null}
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

    '''
        LegacyPlace content spec

        LP_REGEXS = (
            # '4ccffc63f6378cfaace1b1d6.4square'
            (re_compile(r'(?P<PlaceId>[a-z0-9]+)\.4square'), '4square'),

            # '21149144.naver'
            (re_compile(r'(?P<PlaceId>[0-9]+)\.naver'), 'naver'),

            # 'ChIJrTLr-GyuEmsRBfy61i59si0.google'
            (re_compile(r'(?P<PlaceId>[A-za-z0-9_\-]+)\.google'), 'google'),

            # 'http://map.naver.com/local/siteview.nhn?code=21149144'
            (re_compile(r'http://map\.naver\.com/local/siteview.nhn\?code=(?P<PlaceId>[0-9]+)'), 'naver'),

            # 'https://foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6'
            (re_compile(r'https?://foursquare\.com/v/.+/(?P<PlaceId>[a-z0-9]+)'), '4square'),

            # 'http://foursquare.com/v/4ccffc63f6378cfaace1b1d6'
            (re_compile(r'https?://foursquare\.com/v/(?P<PlaceId>[a-z0-9]+)'), '4square'),
        )
    '''

    def test_post_by_current_pos(self):
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
        with open(resized) as f:
            response = self.client.post('/imgs/', dict(file=f))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        img_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(img_uuid)

        # 주소값 조회 : 한국이 아니거나 신주소가 없는 경우에는 주소 하나만 등록하면 됨
        addr_new = '경기도 성남시 분당구 산운로32번길 12'
        addr = '경기도 성남시 분당구 운중동 883-3'

        # 신 주소값 등록 : 없는 경우 pass
        response = self.client.post('/stxts/', dict(content=addr_new))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        addr_new_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(addr_new_uuid)

        # 주소값 등록
        response = self.client.post('/stxts/', dict(content=addr_new))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        addr_new_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(addr_new_uuid)

        # 노트 입력 받기
        note = self.input_from_user('장소 노트')

        # 노트 등록 : 가능한한 빨리 미리 등록
        response = self.client.post('/stxts/', dict(content=note))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        note_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(note_uuid)

        # 드디어! 현재 위치 저장
        # notes 가 list type 이지만 post create 시엔 1개만 가능 : 여러개 필요시 말해주어~
        # image 는 여러개가 가능하지만, 일단 place 를 만든 다음에 추가하는 식으로 UI를 짜는게 좋지 않을까...
        # image 가 여러개인 경우, list 상의 첫번째 사진이 중요. 유저가 방금 찍은 사진이 되도록...
        json_add = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "notes": [{"uuid": "%s", "content": null}],
                "images": [{"uuid": "%s", "content": null, "note": null}]
            }
        ''' % (lon, lat, note_uuid, img_uuid,)
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 결과값에서 userPost, placePost 조회
        result = json_loads(response.content)
        userPost = result['userPost']
        placePost = result['placePost']

        # place_id 조회
        place_id = userPost['place_id']
        self.assertEqual(type(place_id), int)

        # placePost.name == null 이면 장소 정보 수집중... 이라 표시하면 됨
        is_progress = placePost['name'] is None
        self.assertEqual(is_progress, True)

        # 사진 추가 with 사진노트
        with open('image/samples/no_exif_test.jpg') as f:
            response = self.client.post('/imgs/', dict(file=f))
        img_uuid = json_loads(response.content)['uuid']
        note = self.input_from_user('사진 노트')
        response = self.client.post('/stxts/', dict(content=note))
        note_uuid = json_loads(response.content)['uuid']
        json_add = '''
            {
                "place_id": %d,
                "images": [
                    {
                        "uuid": "%s",
                        "content": null,
                        "note": {"uuid": "%s", "content": null}
                    }
                ]
            }
        ''' % (place_id, img_uuid, note_uuid,)
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = json_loads(response.content)
        userPost = result['userPost']
        placePost = result['placePost']

        # Only for server test... (Not interface guide)
        response = self.client.get('/uplaces/?ru=myself')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['userPost'], userPost)
        self.assertEqual(results[0]['placePost'], placePost)


    def test_post_by_url(self):

        # URL 입력 받음
        url = self.input_from_user('http://maukistudio.com/')

        # 프리뷰...
        # URL 에서 뽑은 대표 이미지를 등록?
        # 만약 등록한다면 post:/images/createByUrl 추가 구현 필요
        # 필요하다면 4/6 까지 완성 및 제공

        # URL 등록
        # URL-result 관련 처리를 어떻게 할지 결정하지 못함
        # 협의 필요. 협의 후 4/6 까지 완성 및 제공
        response = self.client.post('/urls/', dict(content=url))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(url_uuid)

        # 노트 입력 받기
        note = self.input_from_user('URL 노트')

        # 노트 등록
        response = self.client.post('/stxts/', dict(content=note))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        note_uuid = json_loads(response.content)['uuid']
        self.assertValidUuid(note_uuid)

        # 드디어! URL 위치 저장
        # urls 가 list type 이지만 post create 시엔 1개만 가능 : 여러개 동시 필요시 말해주어
        json_add = '''
            {
                "notes": [{"uuid": "%s", "content": null}],
                "urls": [{"uuid": "%s", "content": null}]
            }
        ''' % (note_uuid, url_uuid,)
        response = self.client.post('/uplaces/', dict(add=json_add))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 결과값에서 userPost, placePost 조회
        result = json_loads(response.content)
        userPost = result['userPost']
        placePost = result['placePost']

        # place_id 조회
        place_id = userPost['place_id']
        self.assertEqual(type(place_id), int)

        # placePost.name == null 이면 장소 정보 수집중... 이라 표시하면 됨
        is_progress = placePost['name'] is None
        self.assertEqual(is_progress, True)

        # Only for server test... (Not interface guide)
        response = self.client.get('/uplaces/?ru=myself')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['userPost'], userPost)
        self.assertEqual(results[0]['placePost'], placePost)


    def test_post_by_FourSquare(self):

        self.fail()

