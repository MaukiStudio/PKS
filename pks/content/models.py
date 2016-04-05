#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from hashlib import md5
from base64 import b16encode
from django.contrib.gis.db import models
from json import loads as json_loads
from re import compile as re_compile

LP_REGEXS = (
    (re_compile(r'(?P<PlaceId>[a-z0-9]+)\.4square'), '4square'),
    (re_compile(r'(?P<PlaceId>[0-9]+)\.naver'), 'naver'),

    (re_compile(r'http://map\.naver\.com/local/siteview.nhn\?code=(?P<PlaceId>[0-9]+)'), 'naver'),
    (re_compile(r'https?://foursquare\.com/v/.+/(?P<PlaceId>[a-z0-9]+)'), '4square'),
    (re_compile(r'https?://foursquare\.com/v/(?P<PlaceId>[a-z0-9]+)'), '4square'),
)


class LegacyPlace(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    content = models.CharField(max_length=255, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.content

    @property
    def uuid(self):
        return '%s.4square' % b16encode(self.id.bytes)

    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json =json_loads(json)
        result = None
        if 'uuid' in json and json['uuid']:
            _id = UUID(json['uuid'].split('.')[0])
            result = cls.objects.get(id=_id)
        elif 'content' in json and json['content']:
            result, created = cls.objects.get_or_create(content=json['content'])
        return result

    def normalize_content(self):
        for regex in LP_REGEXS:
            searcher = regex[0].search(self.content)
            if searcher:
                self.content = '%s.%s' % (searcher.group('PlaceId'), regex[1])
                return

    def set_id(self):
        splits = self.content.split('.')
        if splits[1] == '4square':
            self.id = UUID(b'00000001%s' % splits[0].rjust(24, b'0'))
        elif splits[1] == 'naver':
            self.id = UUID(b'00000002%s' % splits[0].rjust(24, b'0'))

    def save(self, *args, **kwargs):
        if not self.id and self.content:
            self.normalize_content()
            self.set_id()
        super(LegacyPlace, self).save(*args, **kwargs)


class ShortText(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    content = models.CharField(max_length=255, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.content

    @property
    def uuid(self):
        return '%s.stxt' % b16encode(self.id.bytes)

    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json =json_loads(json)
        result = None
        if 'uuid' in json and json['uuid']:
            _id = UUID(json['uuid'].split('.')[0])
            result = cls.objects.get(id=_id)
        elif 'content' in json and json['content']:
            result, created = cls.objects.get_or_create(content=json['content'])
        return result

    def set_id(self):
        m = md5()
        m.update(self.content.encode(encoding='utf-8'))
        h = m.digest()
        self.id = UUID(b16encode(h))

    def save(self, *args, **kwargs):
        if not self.id and self.content:
            self.set_id()
        super(ShortText, self).save(*args, **kwargs)
