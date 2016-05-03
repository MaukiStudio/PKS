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
