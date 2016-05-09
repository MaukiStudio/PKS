#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404

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

    # queryset 부분만 제외하고는 GenericAPIView.get_object() 와 동일
    def get_object(self):
        queryset = self.queryset
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class ContentViewset(ModelViewSet):

    # MUST overrided
    queryset = None
    serializer_class = None


    # CAN overrided
    def create(self, request, *args, **kwargs):
        ModelClass = self.serializer_class.Meta.model
        raw_content = request.data['content']
        content = ModelClass.normalize_content(raw_content)
        model, is_created = ModelClass.objects.get_or_create(content=content)
        if model.content != content:
            raise HashCollisionError
        serializer = self.get_serializer(model)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

