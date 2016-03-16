#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.auth import SESSION_KEY
from rest_framework.test import APITestCase


class APITestBase(APITestCase):

    def check_login(self, user=None):
        session_key = self.client.session.get(SESSION_KEY)
        if session_key is None:
            return False
        else:
            if user is None:
                return True
            elif user.pk == int(session_key):
                return True
            else:
                self.fail('User in session != User in parameters')

    def assertLogin(self, user=None):
        return self.assertTrue(self.check_login(user))

    def assertNotLogin(self):
        return self.assertFalse(self.check_login())
