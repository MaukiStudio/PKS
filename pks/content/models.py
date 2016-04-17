#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from re import compile as re_compile
from django.contrib.gis.db import models

from base.models import Content
from phonenumbers import parse, format_number, PhoneNumberFormat

LP_REGEXS = (
    # '4ccffc63f6378cfaace1b1d6.4square'
    (re_compile(r'^(?P<PlaceId>[a-z0-9]+)\.4square$'), '4square'),

    # '21149144.naver'
    (re_compile(r'^(?P<PlaceId>[0-9]+)\.naver$'), 'naver'),

    # 'ChIJrTLr-GyuEmsRBfy61i59si0.google'
    (re_compile(r'^(?P<PlaceId>[A-za-z0-9_\-]+)\.google$'), 'google'),
)
LP_REGEXS_URL = (
    # 'http://map.naver.com/local/siteview.nhn?code=21149144'
    (re_compile(r'^http://map\.naver\.com/local/siteview.nhn\?code=(?P<PlaceId>[0-9]+)$'), 'naver'),

    # 'https://foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6'
    (re_compile(r'^https?://foursquare\.com/v/.+/(?P<PlaceId>[a-z0-9]+)$'), '4square'),

    # 'http://foursquare.com/v/4ccffc63f6378cfaace1b1d6'
    (re_compile(r'^https?://foursquare\.com/v/(?P<PlaceId>[a-z0-9]+)$'), '4square'),
)

LP_TYPE = {'4square': 1, 'naver': 2, 'google': 3}


class LegacyPlace(Content):
    place = models.ForeignKey('place.Place', on_delete=models.SET_DEFAULT, null=True, default=None, related_name='lps')
    lp_type = models.SmallIntegerField(blank=True, null=True, default=None)

    def pre_save(self):
        self.lp_type = LP_TYPE[self.contentType]

    class Meta:
        unique_together = ('place', 'lp_type',)

    # MUST override
    @property
    def contentType(self):
        splits = self.content.split('.')
        return splits[1]

    @property
    def accessedType(self):
        splits = self.content.split('.')
        if splits[1] == 'google':
            return 'json'
        else:
            return 'html'

    @classmethod
    def normalize_content(self, raw_content):
        for regex in LP_REGEXS+LP_REGEXS_URL:
            searcher = regex[0].search(raw_content)
            if searcher:
                return '%s.%s' % (searcher.group('PlaceId'), regex[1])

    @property
    def _id(self):
        splits = self.content.split('.')
        if splits[1] == '4square':
            return UUID(b'00000001%s' % splits[0].rjust(24, b'0'))
        elif splits[1] == 'naver':
            return UUID(b'00000002%s' % splits[0].rjust(24, b'0'))
        elif splits[1] == 'google':
            h = self.get_md5_hash(splits[0])
            h0 = hex(int(h[0], 16) | 8)[2:]
            return UUID('%s%s' % (h0, h[1:]))
        else:
            raise NotImplementedError

    @property
    def url_for_access(self):
        self.content = self.normalize_content(self.content)
        splits = self.content.split('.')
        if splits[1] == 'naver':
            return 'http://map.naver.com/local/siteview.nhn?code=%s' % splits[0]
        elif splits[1] == '4square':
            return 'https://foursquare.com/v/%s' % splits[0]
        else:
            # TODO : 구글도 땡겨올 수 있게끔 수정
            raise NotImplementedError


class ShortText(Content):
    # MUST override
    @property
    def contentType(self):
        return 'stxt'

    @property
    def accessedType(self):
        return 'html'


class PhoneNumber(Content):

    # MUST override
    @property
    def contentType(self):
        return 'phone'

    @property
    def accessedType(self):
        return 'txt'


    # CAN override
    @classmethod
    def normalize_content(cls, raw_content):
        # TODO : 국가 관련 처리 개선
        p = parse(raw_content, 'KR')
        r = format_number(p, PhoneNumberFormat.E164)
        return r

    @property
    def _id(self):
        return UUID(self.content[1:].rjust(32, b'0'))

    @property
    def url_for_access(self):
        # 구글 검색 땡겨올 수 있도록 수정
        raise NotImplementedError
        self.content = self.normalize_content(self.content)
        # TODO : 국가 처리
        p = parse(self.content, 'KR')
        r = format_number(p, PhoneNumberFormat.NATIONAL)
        return 'http://www.google.com/#q="%s"' % r


class PlaceName(Content):
    # MUST override
    @property
    def contentType(self):
        return 'pname'

    @property
    def accessedType(self):
        return 'html'


class Address(Content):
    # MUST override
    @property
    def contentType(self):
        return 'addr'

    @property
    def accessedType(self):
        return 'html'


class PlaceNote(Content):
    # MUST override
    @property
    def contentType(self):
        return 'pnote'

    @property
    def accessedType(self):
        return 'html'


class ImageNote(Content):
    # MUST override
    @property
    def contentType(self):
        return 'inote'

    @property
    def accessedType(self):
        return 'html'

