#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from hashlib import md5
from uuid import UUID
from base64 import b16encode
from django.contrib.gis.db import models
from json import loads as json_loads


class Url(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    content = models.URLField(max_length=255, blank=True, null=True, default=None)

    def set_id(self):
        m = md5()
        m.update(self.content)
        h = m.digest()
        self.id = UUID(b16encode(h))

    def save(self, *args, **kwargs):
        if not self.id and self.content:
            self.set_id()
        super(Url, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.content

    @property
    def uuid(self):
        return '%s.url' % b16encode(self.id.bytes)

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
