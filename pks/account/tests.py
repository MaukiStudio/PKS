#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session

from rest_framework.test import APITestCase
from rest_framework import status


class VDViewSetTest(APITestCase):

    def setUp(self):
        self.response1 = self.client.get(reverse('vd-list'))
        self.response2 = self.client.get(reverse('vd-list'), {'format': 'api'})

    def test_can_connect(self):
        self.assertEqual(self.response1.status_code, status.HTTP_200_OK)
        self.assertEqual(self.response2.status_code, status.HTTP_200_OK)

    def test_valid_json(self):
        decoded = json.JSONDecoder().decode(self.response1.content)
        encoded = json.JSONEncoder(separators=(',', ':')).encode(decoded)
        self.assertEqual(encoded, self.response1.content)


class UserLoginTest(APITestCase):

    def test_can_connect_by_browser(self):
        response = self.client.get('/api-auth/login/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_internal(self):
        user = User(username='gulby')
        user.set_password('pass')
        user.save()

        user2 = User.objects.first()
        self.assertEqual(user, user2)

        login_result = self.client.login(username='gulby', password='pass')
        self.assertTrue(login_result)
        self.assertEqual(1, Session.objects.count())

        session = Session.objects.first()
        self.assertEqual(user.pk, int(session.get_decoded().get(SESSION_KEY)))

    def test_login_external(self):
        user = User(username='gulby')
        user.set_password('pass')
        user.save()
        response = self.client.post('/api-auth/login/', {'username': 'gulby', 'password': 'pass'})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, Session.objects.count())
        session = Session.objects.first()
        self.assertEqual(user.pk, int(session.get_decoded().get(SESSION_KEY)))


class UserRegisterTest(APITestCase):

    def test_register_normal(self):
        response = self.client.post('/users/', {'username': 'gulby', 'password': 'pass'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_auto(self):
        response = self.client.post('/users/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)