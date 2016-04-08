#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status

from base.utils import HashCollisionError
from pks.settings import VD_SESSION_KEY
from account.models import VD


class BaseViewset(ModelViewSet):

    # MUST overrided
    queryset = None
    serializer_class = None

    # DOT NOT override
    def __init__(self, *args, **kwargs):
        self._vd = None
        super(BaseViewset, self).__init__(*args, **kwargs)

    @property
    def vd(self):
        if not self._vd:
            vd_id = self.request.session[VD_SESSION_KEY]
            self._vd = VD.objects.get(id=vd_id)
        return self._vd


class ContentViewset(ModelViewSet):

    # MUST overrided
    queryset = None
    serializer_class = None


    # CAN overrided
    def create(self, request, *args, **kwargs):
        ModelClass = self.serializer_class.Meta.model
        raw_content = request.data['content']
        content = ModelClass.normalize_content(raw_content)
        model, created = ModelClass.objects.get_or_create(content=content)
        if model.content != content:
            raise HashCollisionError
        serializer = self.get_serializer(model)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

