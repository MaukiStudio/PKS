#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from base.tests import APITestBase


class FunctionalTestBase(APITestBase):

    def __init__(self, *args, **kwargs):
        self.secureStorage = dict()
        self.normalStorage = dict()
        super(FunctionalTestBase, self).__init__(*args, **kwargs)

    def user_input(self, default):
        return default


class FunctionalTestAfterLoginBase(FunctionalTestBase):

    def setUp(self):
        response = self.client.post('/users/register/')
        self.secureStorage['auth_user_token'] = json_loads(response.content)['auth_user_token']
        response = self.client.post('/users/login/', dict(auth_user_token=self.secureStorage['auth_user_token']))
        email = self.user_input('gulby@maukistudio.com')
        response = self.client.post('/vds/register/', dict(email=email,))
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']
        response = self.client.post('/vds/login/', dict(auth_vd_token=self.normalStorage['auth_vd_token']))
        self.normalStorage['auth_vd_token'] = json_loads(response.content)['auth_vd_token']
        self.assertLogin()
        self.assertVdLogin()
