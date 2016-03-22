#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid1
from base64 import urlsafe_b64encode
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import status

from cryptography.fernet import Fernet
from pks.settings import USER_ENC_KEY, VD_SESSION_KEY
from account import models
from account import serializers


class UserViewset(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    @list_route(methods=['get', 'post'])
    def register(self, request):
        # create user
        username = urlsafe_b64encode(uuid1().bytes).replace('=', '.')
        password = User.objects.make_random_password()
        user = User(username=username)
        user.set_password(password)
        user.save()
        # generate token
        raw_token = '%s|%s|%s' % (user.pk, username, password)
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
        pk = int(raw_token.split('|')[0])
        username = raw_token.split('|')[1]
        password = raw_token.split('|')[2]

        # check credentials
        user = authenticate(username=username, password=password)
        if not user or user.pk != pk or user.is_active is False:
            return Response({'result': False}, status=status.HTTP_401_UNAUTHORIZED)

        # login
        login(request, user)
        return Response({'result': True}, status=status.HTTP_302_FOUND)


class VDViewset(ModelViewSet):
    queryset = models.VD.objects.all()
    serializer_class = serializers.VDSerializer

    def getToken(self, vd):
        raw_token = '%s|%s' % (vd.pk, vd.authOwner.pk)
        encrypter = Fernet(models.getVdEncKey(vd.authOwner))
        return encrypter.encrypt(raw_token.encode(encoding='utf-8'))

    @list_route(methods=['post'])
    def register(self, request):
        # create VD
        # TODO : 여기서 불필요한 aid 계산이 일어남. 제거할 것
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        vd = serializer.instance

        # 추가 처리
        if vd.authOwner is None and request.user.is_authenticated:
            vd.authOwner = request.user
            vd.save()
        if 'email' in request.data:
            vd.authOwner.email = request.data['email']
            vd.authOwner.save()

        # generate token
        token = self.getToken(vd)

        # TODO : send email

        # Temporary : 곧바로 이메일 인증이 된 것으로 처리
        if vd.authOwner and vd.authOwner.email:
            realUser, isCreated = models.RealUser.objects.get_or_create(email=vd.authOwner.email)
            vd.realOwner = realUser
            vd.save()

        # return result
        return Response({'auth_vd_token': token}, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['post'])
    def login(self, request):
        # auth_vd_token
        token = request.data['auth_vd_token']
        decrypter = Fernet(models.getVdEncKey(request.user))
        raw_token = decrypter.decrypt(token.encode(encoding='utf-8'))
        vd_pk = int(raw_token.split('|')[0])
        user_pk = int(raw_token.split('|')[1])

        # check credentials
        try:
            vd = models.VD.objects.get(pk=vd_pk)
        except models.VD.DoesNotExist:
            vd = None
        if vd and vd_pk and vd_pk == vd.pk and user_pk and request.user.is_authenticated()\
                and user_pk == request.user.pk and user_pk == vd.authOwner.pk:
            request.session[VD_SESSION_KEY] = vd_pk
            token = self.getToken(vd)
            return Response({'auth_vd_token': token}, status=status.HTTP_302_FOUND)
        else:
            return Response({'auth_vd_token': None}, status=status.HTTP_401_UNAUTHORIZED)

    @list_route(methods=['get', 'post'])
    def logout(self, request):
        request.session[VD_SESSION_KEY] = None
        del request.session[VD_SESSION_KEY]
        return Response({'result': True}, status=status.HTTP_200_OK)

    def get_object(self):
        aid = self.kwargs['pk']
        if str(aid) == 'mine':
            vd_pk = self.request.session[VD_SESSION_KEY]
        else:
            vd_pk = models.getVidIdFromAid(self.request.user, aid)
        return models.VD.objects.get(pk=vd_pk)


class RealUserViewset(ModelViewSet):
    queryset = models.RealUser.objects.all()
    serializer_class = serializers.RealUserSerializer

    def get_object(self):
        aid = self.kwargs['pk']
        if str(aid) == 'mine' and VD_SESSION_KEY in self.request.session:
            vd_pk = self.request.session[VD_SESSION_KEY]
            if not vd_pk:
                return None
            vd = models.VD.objects.get(pk=vd_pk)
            if not vd:
                return None
            return vd.realOwner
        return super(RealUserViewset, self).get_object()

    @detail_route(methods=['get'])
    def vds(self, request, pk=None):
        ru = self.get_object()
        vd_pk = self.request.session[VD_SESSION_KEY]
        serializer = serializers.VDSerializer(ru.vds.exclude(pk=vd_pk), many=True)
        return Response(serializer.data)

