#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status
from glob import glob

from base.tests import FunctionalTestAfterLoginBase


class ImagesImportScenarioTest(FunctionalTestAfterLoginBase):
    '''
        Importer Guide Json Schema
            {
                "type": "images",
                "vd": "myself"
            }
    '''

    def test_images_import(self):
        # File Upload & Register Image
        for file_name in glob('image/samples/*.jpg'):
            with open(file_name) as f:
                response = self.client.post('/rfs/', dict(file=f))
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                img_url = json_loads(response.content)['file']
                response = self.client.post('/imgs/', dict(content=img_url))
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Importer
        guide_json = '{"type": "images", "vd": "myself"}'
        response = self.client.post('/importers/', dict(guide=guide_json))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ImportedPlaceScenarioTest(FunctionalTestAfterLoginBase):
    # Only for server test... (Not interface guide)
    def setUp(self):
        from account.models import VD
        from place.models import Place, PostPiece
        from importer.models import Proxy, Importer, ImportedPlace
        from place.post import PostBase
        super(ImportedPlaceScenarioTest, self).setUp()
        self.vd_publisher = VD.objects.create()
        self.proxy = Proxy.objects.create(vd=self.vd_publisher)
        self.vd_subscriber = VD.objects.get(id=self.vd_id)
        self.imp = Importer.objects.create(publisher=self.proxy, subscriber=self.vd_subscriber)
        self.place = Place.objects.create()
        self.place2 = Place.objects.create()
        self.iplace = ImportedPlace.objects.create(vd=self.vd_publisher, place=self.place)
        pb = PostBase('{"notes": [{"content": "test note"}]}')
        self.pp = PostPiece.objects.create(place=None, uplace=self.iplace, vd=self.vd_publisher, data=pb.json)
        self.iplace2 = ImportedPlace.objects.create(vd=self.vd_publisher, place=self.place2)

    def test_iplaces_take_drop(self):
        # 아직 처리되지 않은 iplace 목록 조회
        response = self.client.get('/iplaces/?ru=myself&limit=1000&offset=0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        iplace_uuid1 = results[0]['iplace_uuid']
        iplace_uuid2 = results[1]['iplace_uuid']

        # take : iplace 를 uplace 로 전환. 이미 해당 uplace 가 있는 경우 post 추가
        # take 한 iplace 는 더 이상 /iplaces/ 로 조회되지 않음
        response = self.client.post('/iplaces/%s/take/' % iplace_uuid1.split('.')[0])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = json_loads(response.content)
        uplace_uuid1 = result['uplace_uuid']
        self.assertNotEqual(iplace_uuid1, uplace_uuid1)

        # drop : iplace 를 drop (내부적으로는 uplace 로 전환 후 drop).
        # 이미 해당 uplace 가 있는 경우 무시. 이미 존재하는 uplace 를 drop 하려면 delete /uplaces/detail/
        # drop 한 iplace 는 더 이상 /iplaces/ 로 조회되지 않음
        response = self.client.post('/iplaces/%s/drop/' % iplace_uuid2.split('.')[0])
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, '')
