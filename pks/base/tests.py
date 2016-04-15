#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.auth import SESSION_KEY
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.test import APITestCase
from uuid import UUID
from json import loads as json_loads, dumps as json_dumps
from os import system as os_system

from pks.settings import VD_SESSION_KEY, MEDIA_ROOT, WORK_ENVIRONMENT
from requests import get as requests_get
from rest_framework import status
from pathlib2 import Path
from place.post import PostBase

class APITestBase(APITestCase):

    def setUp(self):
        self.clear_media_files()

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

    def uploadFile(self, file_name):
        f = open('image/samples/%s' % file_name, 'rb')
        ff = File(f)
        result = InMemoryUploadedFile(ff, None, file_name, None, ff.size, None, None)
        return result

    def assertValidUuid(self, uuid_json):
        hex_str = uuid_json.split('.')[0]
        type_str = uuid_json.split('.')[1]
        _uuid = UUID(hex_str)
        self.assertEqual(type(_uuid), UUID)
        return self.assertIn(type_str, ('img', 'stxt', 'url', '4square', 'naver', 'google', 'uplace',))

    def printJson(self, json):
        if type(json) is dict:
            json = json_dumps(json)
        elif type(json) is PostBase:
            json = json_dumps(json.json)
        print(json)
        print('')

    @property
    def vd_id(self):
        vd_id = None
        if VD_SESSION_KEY in self.client.session:
            vd_id = self.client.session[VD_SESSION_KEY]
        return vd_id

    def clear_media_files(self):
        if WORK_ENVIRONMENT:
            os_system('rm -rf %s' % MEDIA_ROOT)

    def assertValidInternetUrl(self, url):
        self.assertEqual(url.startswith('http'), True)
        r = requests_get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def assertValidLocalFile(self, path):
        path = Path(path)
        self.assertEqual(path.exists(), True)

    def assertIsSubsetOf(self, A, B):
        result = isSubsetOf(A, B)
        if not result:
            self.printJson(A)
            self.printJson(B)
            self.fail('assertIsSubsetOf() fail')

    def assertIsNotSubsetOf(self, A, B):
        result = isSubsetOf(A, B)
        if result:
            self.printJson(A)
            self.printJson(B)
            self.fail('assertIsNotSubsetOf() fail')


class FunctionalTestBase(APITestBase):

    def __init__(self, *args, **kwargs):
        self.secureStorage = dict()
        self.normalStorage = dict()
        super(FunctionalTestBase, self).__init__(*args, **kwargs)

    def input_from_user(self, default='gulby@maukistudio.com'):
        return default

    def get_gps_info(self, default=(127.0, 37.0)):
        return default

    def take_picture(self, default='image/samples/test.jpg'):
        return default

    def resize_image(self, default='image/samples/test.jpg'):
        return default


class FunctionalTestAfterLoginBase(FunctionalTestBase):

    def setUp(self):
        super(FunctionalTestAfterLoginBase, self).setUp()
        response = self.client.post('/users/register/')
        self.secureStorage['auth_user_token'] = json_loads(response.content)['auth_user_token']
        response = self.client.post('/users/login/', dict(auth_user_token=self.secureStorage['auth_user_token']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        email = self.input_from_user()
        response = self.client.post('/vds/register/', dict(email=email,))
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']
        response = self.client.post('/vds/login/', dict(auth_vd_token=self.normalStorage['auth_vd_token']))
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']
        self.assertLogin()
        self.assertVdLogin()

def isSubsetOf(self, other):
    def isSubsetOf_dict(d1, d2):
        if not d1: return True
        elif not d2: return False
        elif type(d2) is not dict: return False

        for key, value in d1.iteritems():
            if not value:
                continue
            elif type(value) is dict:
                if key not in d2 or not isSubsetOf_dict(value, d2[key]):
                    return False
            elif type(value) is list:
                if key not in d2 or not isSubsetOf_list(value, d2[key]):
                    return False
            else:
                if key not in d2 or value != d2[key]:
                    return False
        return True
    def isSubsetOf_list(l1, l2):
        if not l1: return True
        elif not l2: return False
        elif type(l2) is not list: return False
        elif len(l1) != len(l2): return False

        for key, value in enumerate(l1):
            if not value:
                if l2[key]:
                    return False
            elif type(value) is dict:
                if not isSubsetOf_dict(value, l2[key]):
                    return False
            elif type(value) is list:
                if not isSubsetOf_list(value, l2[key]):
                    return False
            else:
                if value != l2[key]:
                    return False
        return True

    if type(self) is PostBase:
        self = self.json
    elif type(self) is unicode or type(self) is str:
        self = json_loads(self)

    if type(other) is PostBase:
        other = other.json
    elif type(other) is unicode or type(other) is str:
        other = json_loads(other)

    return isSubsetOf_dict(self, other)
