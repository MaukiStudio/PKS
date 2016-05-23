#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import FunctionalTestAfterLoginBase


class StorageScenarioTest(FunctionalTestAfterLoginBase):

    def test_read_storages(self):
        response = self.client.get('/storages/test_key/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(result['value'], None)

    def test_write_storage(self):
        json = '{"sub_key": "sample value"}'
        response = self.client.patch('/storages/new_key/', dict(value=json))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json_loads(response.content)
        self.assertEqual(result['value'], json)
