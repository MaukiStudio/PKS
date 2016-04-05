#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.auth import SESSION_KEY
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.test import APITestCase
from uuid import UUID
from json import dumps as json_dumps

from pks.settings import VD_SESSION_KEY


class APITestBase(APITestCase):

    def check_login(self, user=None):
        session_key = self.client.session.get(SESSION_KEY)
        if session_key and (not user or session_key == unicode(user.id)):
            return True
        return False

    def assertLogin(self, user=None):
        return self.assertTrue(self.check_login(user))

    def assertNotLogin(self):
        return self.assertFalse(self.check_login())

    def check_vd_login(self, vd=None):
        vd_id_str = self.client.session.get(VD_SESSION_KEY)
        if vd_id_str and (not vd or vd_id_str == vd.id):
            return True
        return False

    def assertVdLogin(self, vd=None):
        return self.assertTrue(self.check_vd_login(vd))

    def assertVdNotLogin(self):
        return self.assertFalse(self.check_vd_login())

    def logout(self):
        if SESSION_KEY in self.client.session:
            self.client.session[SESSION_KEY] = None
            del self.client.session[SESSION_KEY]
        self.client.logout()

    def uploadImage(self, img_file_name):
        f = open('image/samples/%s' % img_file_name, 'rb')
        ff = File(f)
        result = InMemoryUploadedFile(ff, None, img_file_name, 'image/jpeg', ff.size, None, None)
        return result

    def assertValidUuid(self, uuid_json):
        hex_str = uuid_json.split('.')[0]
        type_str = uuid_json.split('.')[1]
        _uuid = UUID(hex_str)
        self.assertEqual(type(_uuid), UUID)
        return self.assertIn(type_str, ('img', 'stxt', 'url', '4square', 'naver', 'google',))

    def printJson(self, json):
        if type(json) is dict:
            json = json_dumps(json)
        print(json)

