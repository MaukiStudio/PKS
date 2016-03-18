#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.auth import SESSION_KEY
from rest_framework.test import APITestCase

from pks.settings import VD_SESSION_KEY


class APITestBase(APITestCase):

    def check_login(self, user=None):
        session_key = self.client.session.get(SESSION_KEY)
        if session_key and (not user or session_key == str(user.pk)):
            return True
        return False

    def assertLogin(self, user=None):
        return self.assertTrue(self.check_login(user))

    def assertNotLogin(self):
        return self.assertFalse(self.check_login())

    def check_vd_login(self, vd=None):
        vd_pk_str = self.client.session.get(VD_SESSION_KEY)
        if vd_pk_str and (not vd or vd_pk_str == vd.pk):
            return True
        return False

    def assertVdLogin(self, vd=None):
        return self.assertTrue(self.check_vd_login(vd))

    def assertVdNotLogin(self):
        return self.assertFalse(self.check_vd_login())

    def logout(self):
        self.client.session[SESSION_KEY] = None
        self.client.logout()


