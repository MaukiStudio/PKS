#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from pks.settings import VD_SESSION_KEY
from account.models import VD


class BaseSerializer(ModelSerializer):
    # DOT NOT override
    def __init__(self, *args, **kwargs):
        self._vd = None
        super(BaseSerializer, self).__init__(*args, **kwargs)

    @property
    def vd(self):
        if not self._vd:
            vd_id = self._context['request'].session[VD_SESSION_KEY]
            self._vd = VD.objects.get(id=vd_id)
        return self._vd


class ContentSerializer(BaseSerializer):
    uuid = ReadOnlyField()
