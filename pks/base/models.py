#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from hashlib import md5
from base64 import b16encode
from django.contrib.gis.db import models
from json import loads as json_loads
from re import compile as re_compile


class Content(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    content = models.CharField(max_length=254, blank=True, null=True, default=None)

    class Meta:
        abstract = True

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
        h = m.hexdigest()
        self.id = UUID(h)

    def save(self, *args, **kwargs):
        if not self.id and self.content:
            self.set_id()
        super(Content, self).save(*args, **kwargs)
