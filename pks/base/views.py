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
            if VD_SESSION_KEY in self.request.session:
                # Session Authentication
                vd_id = self.request.session[VD_SESSION_KEY]
                self._vd = VD.objects.get(id=vd_id)
            else:
                # Token Authentication
                # TODO : account 쪽과 중복. 리팩토링~
                from cryptography.fernet import Fernet
                from pks.settings import USER_ENC_KEY
                from django.contrib.auth import authenticate
                if 'auth_user_token' in self.request.data:
                    auth_user_token = self.request.data['auth_user_token']
                    auth_vd_token = self.request.data['auth_vd_token']
                elif 'auth_user_token' in self.request.query_params:
                    auth_user_token = self.request.query_params['auth_user_token']
                    auth_vd_token = self.request.query_params['auth_vd_token']
                else:
                    return None

                # user auth
                decrypter = Fernet(USER_ENC_KEY)
                raw_token = decrypter.decrypt(auth_user_token.encode(encoding='utf-8'))
                user_id = int(raw_token.split('|')[0])
                username = raw_token.split('|')[1]
                password = raw_token.split('|')[2]
                user = authenticate(username=username, password=password)
                if not user or user.id != user_id or user.is_active is False:
                    return None

                # VD auth
                decrypter = Fernet(user.crypto_key)
                raw_token = decrypter.decrypt(auth_vd_token.encode(encoding='utf-8'))
                vd_id = int(raw_token.split('|')[0])
                user_id = int(raw_token.split('|')[1])
                vd = VD.objects.get(id=vd_id)
                if vd and vd_id and vd_id == vd.id and user_id and user_id == user.id and user_id == vd.authOwner_id:
                    self._vd = vd
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
        instance, is_created = ModelClass.get_or_create_smart(request.data['content'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

