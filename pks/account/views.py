#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid1
from base64 import urlsafe_b64encode
from django.contrib.auth import login, authenticate
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.contrib.gis.geos import GEOSGeometry
from json import loads as json_loads
from django.shortcuts import redirect

from cryptography.fernet import Fernet
from pks.settings import USER_ENC_KEY, VD_SESSION_KEY
from account.models import User, RealUser, VD, Storage, Tracking
from account.serializers import UserSerializer, RealUserSerializer, VDSerializer, StorageSerializer, TrackingSerializer
from base.views import BaseViewset
from base.utils import get_timestamp


class UserViewset(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @list_route(methods=['post'])
    def register(self, request):
        # create user
        username = urlsafe_b64encode(uuid1().bytes).replace('=', '.')
        password = User.objects.make_random_password()
        user = User(username=username)
        user.set_password(password)
        user.save()
        # generate token
        raw_token = '%s|%s|%s' % (user.id, username, password)
        encrypter = Fernet(USER_ENC_KEY)
        token = encrypter.encrypt(raw_token.encode(encoding='utf-8'))
        # return result
        return Response({'auth_user_token': token}, status=status.HTTP_201_CREATED)

    @list_route(methods=['post'])
    def login(self, request):
        # auth_user_token
        token = request.data['auth_user_token']
        decrypter = Fernet(USER_ENC_KEY)
        raw_token = decrypter.decrypt(token.encode(encoding='utf-8'))
        splits = raw_token.split('|')
        user_id = int(splits[0])
        username = splits[1]
        password = splits[2]

        # check credentials
        user = authenticate(username=username, password=password)
        if not user or user.id != user_id or user.is_active is False:
            return Response({'result': False}, status=status.HTTP_401_UNAUTHORIZED)

        # login
        login(request, user)
        return Response({'result': True}, status=status.HTTP_200_OK)


class VDViewset(ModelViewSet):
    queryset = VD.objects.all()
    serializer_class = VDSerializer

    @list_route(methods=['post'])
    def register(self, request):
        if not request.user.is_authenticated():
            return Response({'auth_vd_token': None}, status=status.HTTP_401_UNAUTHORIZED)

        # create VD
        # TODO : 여기서 불필요한 aid 계산이 일어남. 제거할 것
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        vd = serializer.instance

        # 추가 처리
        if vd.authOwner is None:
            vd.authOwner = request.user
            vd.save()
        if 'email' in request.data:
            email = request.data['email']
            vd.authOwner.email = email
            vd.authOwner.save()
            if email.split('@')[1] in ('facebook.auth', 'kakaotalk.auth'):
                realUser, is_created = RealUser.objects.get_or_create(email=email)
                vd.realOwner = realUser
                vd.save()

        # send confirm email
        if not vd.realOwner and vd.authOwner and vd.authOwner.email:
            vd.send_confirm_email(vd.authOwner.email)
        # return result
        return Response({'auth_vd_token': vd.getToken()}, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['post'])
    def login(self, request):
        # auth_vd_token
        token = request.data['auth_vd_token']
        decrypter = Fernet(request.user.crypto_key)
        raw_token = decrypter.decrypt(token.encode(encoding='utf-8'))
        splits = raw_token.split('|')
        vd_id = int(splits[0])
        user_id = int(splits[1])

        # check credentials
        try:
            vd = VD.objects.get(id=vd_id)
        except VD.DoesNotExist:
            vd = None
        if vd and vd_id and vd_id == vd.id and user_id and request.user.is_authenticated()\
                and user_id == request.user.id and user_id == vd.authOwner_id:
            request.session[VD_SESSION_KEY] = vd_id
            token = vd.getToken()
            from account.task_wrappers import AfterLoginTaskWrapper
            task = AfterLoginTaskWrapper()
            task.delay(vd_id)
            return Response({'auth_vd_token': token}, status=status.HTTP_200_OK)
        else:
            return Response({'auth_vd_token': None}, status=status.HTTP_401_UNAUTHORIZED)

    @list_route(methods=['get'])
    def confirm(self, request):
        # email_confirm_token
        token = request.query_params['email_confirm_token']
        from pks.settings import VD_ENC_KEY
        decrypter = Fernet(VD_ENC_KEY)
        raw_token = decrypter.decrypt(token.encode(encoding='utf-8'))
        splits = raw_token.split('|')
        vd_id = int(splits[0])
        email = splits[1]

        # check credentials and confirm email
        vd = VD.objects.get(id=vd_id)
        if vd and vd_id and email:
            from base.cache import cache_clear_ru
            realUser, is_created = RealUser.objects.get_or_create(email=email)
            if vd.realOwner:
                cache_clear_ru(vd.realOwner)
            vd.realOwner = realUser
            vd.save()
            cache_clear_ru(realUser)
            return redirect('/ui/confirm_ok/')
        else:
            return redirect('/ui/confirm_fail/')

    @list_route(methods=['get', 'post'])
    def logout(self, request):
        request.session[VD_SESSION_KEY] = None
        del request.session[VD_SESSION_KEY]
        return Response({'result': True}, status=status.HTTP_200_OK)

    def get_object(self):
        aid = self.kwargs['pk']
        if unicode(aid) == 'myself':
            vd_id = self.request.session[VD_SESSION_KEY]
        else:
            vd_id = self.request.user.aid2id(aid)
        return VD.objects.get(id=vd_id)


class RealUserViewset(ModelViewSet):
    queryset = RealUser.objects.all()
    serializer_class = RealUserSerializer

    def get_object(self):
        aid = self.kwargs['pk']
        if unicode(aid) == 'myself' and VD_SESSION_KEY in self.request.session:
            vd_id = self.request.session[VD_SESSION_KEY]
            vd = VD.objects.get(id=vd_id)
            if vd.realOwner:
                return vd.realOwner
        return super(RealUserViewset, self).get_object()

    @detail_route(methods=['get'])
    def vds(self, request, pk=None):
        ru = self.get_object()
        vd_id = self.request.session[VD_SESSION_KEY]
        serializer = VDSerializer(ru.vds.exclude(id=vd_id), many=True)
        return Response(serializer.data)


class StorageViewset(BaseViewset):
    queryset = Storage.objects.all()
    serializer_class = StorageSerializer

    def get_object(self):
        key = self.kwargs['pk']
        vd = self.vd
        if not vd:
            raise Http404
        result, is_created = Storage.objects.get_or_create(vd=vd, key=key)
        return result

    def perform_create(self, serializer):
        serializer.save(vd=self.vd)


class TrackingViewset(BaseViewset):
    queryset = Tracking.objects.all()
    serializer_class = TrackingSerializer

    def create(self, request, *args, **kwargs):
        vd = self.vd
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)
        v = json_loads(request.data['value'])
        lonLat = GEOSGeometry('POINT(%f %f)' % (v['lon'], v['lat']), srid=4326)
        timestamp = request.data.get('timestamp', get_timestamp())
        instance = Tracking.create(vd.id, lonLat, timestamp)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
