#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from rest_framework import status

from base.tests import FunctionalTestAfterLoginBase
from etc.models import Notice, Inquiry
from account.models import RealUser


class NoticeViewsetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(NoticeViewsetTest, self).setUp()
        self.notice = Notice.objects.create(title='test notice', data='{"k1": "v1", "k2": "v2"}')

    def test_list(self):
        response = self.client.get('/notices/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

    def test_create(self):
        self.assertEqual(Notice.objects.count(), 1)
        response = self.client.post('/notices/', dict(title='notice2', data='{"k1": "v1", "k2": "v2", "content": "blah blah"}'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notice.objects.count(), 2)
        result = json_loads(response.content)
        self.assertEqual(result['title'], 'notice2')
        self.assertIn('content', result['data'])


class InquiryViewsetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(InquiryViewsetTest, self).setUp()
        self.ru = self.vd.realOwner
        self.inquiry = Inquiry.objects.create(ru=self.ru, data='{"k1": "v1", "k2": "v2"}')

    def test_list(self):
        response = self.client.get('/inquiries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

        other_ru = RealUser.objects.create(email='other@maukistudio.com')
        self.assertEqual(Inquiry.objects.count(), 1)
        other_inquiry = Inquiry.objects.create(ru=other_ru, data='{"k1": "v1", "k2": "v2"}')
        self.assertEqual(Inquiry.objects.count(), 2)

        response = self.client.get('/inquiries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 1)

    def test_create(self):
        self.assertEqual(Inquiry.objects.count(), 1)
        response = self.client.post('/inquiries/', dict(data='{"k1": "v1", "k2": "v2", "content": "blah blah"}'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inquiry.objects.count(), 2)
        result = json_loads(response.content)
        self.assertEqual(result['ru'], self.vd.realOwner.id)
        self.assertIn('content', result['data'])

        response = self.client.get('/inquiries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json_loads(response.content)['results']
        self.assertEqual(type(results), list)
        self.assertEqual(len(results), 2)
