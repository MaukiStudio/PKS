#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from hashlib import md5
from base64 import b16encode
from django.contrib.gis.db import models
from json import loads as json_loads
from os.path import join as os_path_join
from rest_framework import status

from base.utils import HashCollisionError
from requests import get as requests_get
from pks.settings import MEDIA_ROOT, MEDIA_URL, SERVER_HOST
from pathlib2 import Path


class Content(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    content = models.CharField(max_length=254, blank=True, null=True, default=None)

    class Meta:
        abstract = True

    # MUST override
    @property
    def contentType(self):
        raise NotImplementedError

    @property
    def accessedType(self):
        raise NotImplementedError

    # CAN override
    @classmethod
    def normalize_content(cls, raw_content):
        return raw_content.strip()

    @property
    def _id(self):
        return UUID(Content.get_md5_hash(self.content))

    def pre_save(self):
        pass

    def post_save(self):
        pass

    @property
    def url_for_access(self):
        _url = self.content.strip()
        if _url.startswith('http'):
            return _url

        # TODO : 구글도 땡겨올 수 있게끔 수정
        raise NotImplementedError
        #return 'https://www.google.com/#q="%s"' % _url

    # MAYBE NOT override
    def __unicode__(self):
        return self.content

    @property
    def uuid(self):
        return '%s.%s' % (b16encode(self.id.bytes), self.contentType,)

    # DO NOT override
    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json =json_loads(json)
        result = None
        if 'uuid' in json and json['uuid']:
            _id = UUID(json['uuid'].split('.')[0])
            result = cls.objects.get(id=_id)
        elif 'content' in json and json['content']:
            content = cls.normalize_content(json['content'])
            result, created = cls.objects.get_or_create(content=content)
            if result.content != content:
                raise HashCollisionError
        return result

    @classmethod
    def get_md5_hash(cls, v):
        m = md5()
        m.update(v.encode(encoding='utf-8'))
        return m.hexdigest()

    def save(self, *args, **kwargs):
        # id/content 처리
        if not self.content:
            raise AssertionError
        self.content = self.normalize_content(self.content)
        _id = self._id
        if self.id and self.id != _id:
            raise NotImplementedError

        # 저장
        self.id = _id
        self.pre_save()
        super(Content, self).save(*args, **kwargs)
        self.post_save()

    # Methods for access
    def access_force(self):
        headers = {'user-agent': 'Chrome'}
        r = requests_get(self.url_for_access, headers=headers)
        if r.status_code not in (status.HTTP_200_OK,):
            raise ValueError('Not valid url_for_access')
        file = Path(self.path_accessed)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        summary = Path(self.path_summarized)
        if not Path(self.path_summarized).parent.exists():
            summary.parent.mkdir(parents=True)
        file.write_bytes(r.content)

    def access_local(self, source):
        file = Path(self.path_accessed)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        summary = Path(self.path_summarized)
        if not Path(self.path_summarized).parent.exists():
            summary.parent.mkdir(parents=True)
        file.symlink_to(source)

    def access(self):
        if not self.id:
            raise NotImplementedError
        if not self.is_accessed:
            # TODO : 로컬 URL 인 경우 access_local() 을 호출하도록 수정
            self.access_force()

    @property
    def is_accessed(self):
        file = Path(self.path_accessed)
        return file.exists()

    @property
    def uuid_accessed(self):
        return '%s.%s' % (self.uuid, self.accessedType,)

    @property
    def path_accessed(self):
        splits = self.uuid.split('.')
        return os_path_join(MEDIA_ROOT, 'accessed', splits[1], splits[0][-3:], self.uuid_accessed)

    @property
    def url_accessed(self):
        splits = self.uuid.split('.')
        return '%s%s%s/%s/%s/%s' % (SERVER_HOST, MEDIA_URL, 'accessed', splits[1], splits[0][-3:], self.uuid_accessed)

    # Methods for thumbnail
    def summarize_force(self, accessed=None):
        raise NotImplementedError

    def summarize(self, accessed=None):
        if not self.id:
            raise NotImplementedError
        if not self.is_summarized:
            if not self.is_accessed:
                self.access_force()
            self.summarize_force(accessed)

    @property
    def is_summarized(self):
        file = Path(self.path_summarized)
        return file.exists()

    @property
    def uuid_summarized(self):
        return '%s.%s.%s' % (self.uuid, 'summary', self.accessedType,)

    @property
    def path_summarized(self):
        splits = self.uuid.split('.')
        return os_path_join(MEDIA_ROOT, 'summary', splits[1], splits[0][-3:], self.uuid_summarized)

    @property
    def url_summarized(self):
        splits = self.uuid.split('.')
        return '%s%s%s/%s/%s/%s' % (SERVER_HOST, MEDIA_URL, 'summary', splits[1], splits[0][-3:], self.uuid_summarized)

    @property
    def content_summarized(self):
        raise NotImplementedError('Must be overrided')
