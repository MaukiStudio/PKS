#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from hashlib import md5
from base64 import b16encode
from django.contrib.gis.db import models
from json import loads as json_loads

from base.utils import HashCollisionError


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
    def normalize_content(cls, raw_content, *args, **kwargs):
        return raw_content.strip()

    @property
    def _id(self):
        return UUID(Content.get_md5_hash(self.content))

    def pre_save(self):
        pass


    # MAYBE NOT override
    def __unicode__(self):
        return self.content

    @property
    def uuid(self):
        return '%s.%s' % (b16encode(self.id.bytes), self.contentType,)

    @property
    def accessed(self):
        return '%s.%s' % (self.uuid, self.accessedType,)


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
            result, created = cls.objects.get_or_create(content=json['content'])
            if result.content != json['content']:
                raise HashCollisionError
        return result

    @classmethod
    def get_md5_hash(self, v):
        m = md5()
        m.update(v.encode(encoding='utf-8'))
        return m.hexdigest()

    def save(self, *args, **kwargs):
        # id/content 처리
        if not self.content:
            raise NotImplementedError
        self.content = self.normalize_content(self.content)
        _id = self._id
        if self.id and self.id != _id:
            raise NotImplementedError

        # 저장
        self.id = _id
        self.pre_save()
        super(Content, self).save(*args, **kwargs)
