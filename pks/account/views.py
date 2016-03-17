#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid1
from base64 import urlsafe_b64encode
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import status

from cryptography.fernet import Fernet
from pks.settings import USER_ENC_KEY, VD_ENC_KEY
from account import models
from account import serializers


class UserViewset(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    @list_route(methods=['post'])
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

    @list_route(methods=['post'])
    def register(self, request):
        # create VD
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        vd = serializer.instance
        vd.owner = request.user
        vd.save()

        # generate token
        raw_token = '%s|%s' % (vd.pk, request.user.pk)
        encrypter = Fernet(VD_ENC_KEY)
        token = encrypter.encrypt(raw_token.encode(encoding='utf-8'))

        # return result
        return Response({'auth_vd_token': token}, status=status.HTTP_201_CREATED, headers=headers)
