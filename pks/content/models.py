#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from hashlib import md5
from re import compile as re_compile

from base.models import Content
from phonenumbers import parse, format_number, PhoneNumberFormat


LP_REGEXS = (
    # '4ccffc63f6378cfaace1b1d6.4square'
    (re_compile(r'^(?P<PlaceId>[a-z0-9]+)\.4square$'), '4square'),

    # '21149144.naver'
    (re_compile(r'^(?P<PlaceId>[0-9]+)\.naver$'), 'naver'),

    # 'ChIJrTLr-GyuEmsRBfy61i59si0.google'
    (re_compile(r'^(?P<PlaceId>[A-za-z0-9_\-]+)\.google$'), 'google'),

    # 'http://map.naver.com/local/siteview.nhn?code=21149144'
    (re_compile(r'^http://map\.naver\.com/local/siteview.nhn\?code=(?P<PlaceId>[0-9]+)$'), 'naver'),

    # 'https://foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6'
    (re_compile(r'^https?://foursquare\.com/v/.+/(?P<PlaceId>[a-z0-9]+)$'), '4square'),

    # 'http://foursquare.com/v/4ccffc63f6378cfaace1b1d6'
    (re_compile(r'^https?://foursquare\.com/v/(?P<PlaceId>[a-z0-9]+)$'), '4square'),
)


class LegacyPlace(Content):

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
        for regex in LP_REGEXS:
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
            # TODO : 나중에 튜닝하기 ㅠ_ㅜ
            m = md5()
            m.update(splits[0].encode(encoding='utf-8'))
            h = m.hexdigest()
            h0 = hex(int(h[0], 16) | 8)[2:]
            return UUID('%s%s' % (h0, h[1:]))
        else:
            raise NotImplementedError


class ShortText(Content):
    # MUST override
    @property
    def contentType(self):
        return 'stxt'

    @property
    def accessedType(self):
        return 'txt'


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
