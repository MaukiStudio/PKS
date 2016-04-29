#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from uuid import uuid1
from base64 import b16encode
from django.contrib.gis.geos import GEOSGeometry
from re import compile as re_compile

from base.tests import APITestBase
#from importer.models import Importer, UserImporter


'''
class ImporterTest(APITestBase):

    def test_string_representation(self):
        imp = Importer()
        test_data = '{"type": "images", "vd": "myself"}'
        img.content = test_data
        img.save()
        self.assertEqual(unicode(img), img.content)
        self.assertEqual(img.uuid, '%s.img' % b16encode(img.id.bytes))

    def test_save_and_retreive(self):
        img = models.Image()
        test_data = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img.content = test_data
        img.save()
        saved = models.Image.objects.first()

        self.assertEqual(saved, img)
        saved2 = models.Image.get_from_json('{"uuid": "%s", "content": null}' % img.uuid)
        self.assertEqual(saved2, img)
        saved3 = models.Image.get_from_json('{"uuid": "%s", "content": null, "note": {"uuid": null, "content": null}}' % img.uuid)
        self.assertEqual(saved3, img)
        saved4 = models.Image.get_from_json('{"uuid": null, "content": "%s"}' % img.content)
        self.assertEqual(saved4, img)
'''
