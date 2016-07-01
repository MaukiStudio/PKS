#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from hashlib import md5
from base64 import b16encode
from django.contrib.gis.db import models
from json import loads as json_loads
from os.path import join as os_path_join
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry

from base.utils import HashCollisionError
from requests import get as requests_get
from pks.settings import MEDIA_ROOT, MEDIA_URL, SERVER_HOST
from pathlib2 import Path


class Point(object):
    def __init__(self, lonLat):
        self.lonLat = lonLat
        self.timestamp = None

    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json =json_loads(json)
        lonLat = GEOSGeometry('POINT(%f %f)' % (json['lon'], json['lat']), srid=4326)
        result = cls(lonLat)
        result.timestamp = 'timestamp' in json and json['timestamp'] or None
        return result

    @property
    def json(self):
        if self.timestamp:
            return dict(lon=self.lonLat.x, lat=self.lonLat.y, timestamp=self.timestamp)
        return dict(lon=self.lonLat.x, lat=self.lonLat.y)
    @property
    def cjson(self):
        return self.json
    @property
    def ujson(self):
        return self.json

    def __eq__(self, other):
        return self.lonLat.__eq__(other.lonLat)


class Visit(object):
    def __init__(self, content):
        self.content = content
        self.timestamp = None

    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json =json_loads(json)
        content = json['content']
        result = cls(content)
        result.timestamp = 'timestamp' in json and json['timestamp'] or None
        return result

    @property
    def json(self):
        if self.timestamp:
            return dict(content=self.content, timestamp=self.timestamp)
        return dict(content=self.content)
    @property
    def cjson(self):
        return self.json
    @property
    def ujson(self):
        return self.json

    def __eq__(self, other):
        return self.content == other.content


class Rating(object):
    def __init__(self, content):
        self.content = content
        self.timestamp = None

    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json =json_loads(json)
        content = json['content']
        result = cls(content)
        result.timestamp = 'timestamp' in json and json['timestamp'] or None
        return result

    @property
    def json(self):
        if self.timestamp:
            return dict(content=self.content, timestamp=self.timestamp)
        return dict(content=self.content)
    @property
    def cjson(self):
        return self.json
    @property
    def ujson(self):
        return self.json

    def __eq__(self, other):
        return self.content == other.content


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
    # TODO : object method 로 전환하고 튜닝 (캐싱 등)
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

    @classmethod
    def on_create(cls, instance):
        pass

    @property
    def json(self):
        if self.timestamp:
            return dict(uuid=self.uuid, content=self.content, timestamp=self.timestamp)
        return dict(uuid=self.uuid, content=self.content)
    @property
    def cjson(self):
        return dict(content=self.content)
    @property
    def ujson(self):
        return dict(uuid=self.uuid)

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
    def __init__(self, *args, **kwargs):
        self.timestamp = None
        self._cache_accessed = None
        self._cache_normalized_content = None
        super(Content, self).__init__(*args, **kwargs)

    @classmethod
    def get_or_create_smart(cls, raw_content):
        content = cls.normalize_content(raw_content)
        if not content:
            raise NotImplementedError
        result, is_created = cls.objects.get_or_create(content=content)
        if result.content != content:
            print(raw_content)
            print(content)
            print(result.content)
            raise HashCollisionError
        if is_created:
            cls.on_create(result)
        return result, is_created

    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json =json_loads(json)
        result = None
        if 'uuid' in json and json['uuid']:
            _id = UUID(json['uuid'].split('.')[0])
            try:
                result = cls.objects.get(id=_id)
            except cls.DoesNotExist:
                pass
        if not result and 'content' in json and json['content']:
            result, is_created = cls.get_or_create_smart(json['content'])
        if result and 'timestamp' in json:
            result.timestamp = json['timestamp']
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
        _id = self._id
        if self.id and self.id != _id:
            raise NotImplementedError

        # 저장
        self.id = _id
        self.pre_save()
        super(Content, self).save(*args, **kwargs)
        self.post_save()

    # Methods for access
    def access_force(self, timeout=3):
        headers = {'user-agent': 'Chrome'}
        r = requests_get(self.url_for_access, headers=headers, timeout=timeout)
        if r.status_code not in (status.HTTP_200_OK,):
            print('Access failed : %s' % self.url_for_access)

        file = Path(self.path_accessed)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        summary = Path(self.path_summarized)
        if not Path(self.path_summarized).parent.exists():
            summary.parent.mkdir(parents=True)
        file.write_text(r.text)
        self._cache_accessed = r.text.replace('\r', '')

    def access_local(self, source):
        file = Path(self.path_accessed)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        summary = Path(self.path_summarized)
        if not Path(self.path_summarized).parent.exists():
            summary.parent.mkdir(parents=True)
        if file.exists():
            file.unlink()
        file.symlink_to(source)

    def access(self, timeout=3):
        if not self.id:
            raise NotImplementedError
        if not self.is_accessed:
            # TODO : 로컬 URL 인 경우 access_local() 을 호출하도록 수정
            self.access_force(timeout=timeout)

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

    # Methods for summary(thumbnail)
    def summarize_force(self, accessed=None):
        raise NotImplementedError

    def summarize(self, accessed=None, timeout=3):
        if not self.id:
            raise NotImplementedError
        if not self.is_summarized:
            if not accessed and not self.is_accessed:
                self.access_force(timeout=timeout)
            self.summarize_force(accessed)

    @property
    def is_summarized(self):
        file = Path(self.path_summarized)
        return file.exists()

    @property
    def summarizedType(self):
        return self.accessedType

    @property
    def uuid_summarized(self):
        return '%s.%s.%s' % (self.uuid, 'summary', self.summarizedType,)

    @property
    def path_summarized(self):
        splits = self.uuid.split('.')
        return os_path_join(MEDIA_ROOT, 'summary', splits[1], splits[0][-3:], self.uuid_summarized)

    @property
    def url_summarized(self):
        splits = self.uuid.split('.')
        return '%s%s%s/%s/%s/%s' % (SERVER_HOST, MEDIA_URL, 'summary', splits[1], splits[0][-3:], self.uuid_summarized)

    @property
    def content_accessed(self):
        if not self._cache_accessed:
            file = Path(self.path_accessed)
            self._cache_accessed = file.read_text()
        return self._cache_accessed

    def _clearCache(self):
        self._cache_accessed = None

    @property
    def content_summarized(self):
        raise NotImplementedError
