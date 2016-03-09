#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid1
from base64 import urlsafe_b64encode
from django.contrib.auth.models import User
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import status

from cryptography.fernet import Fernet
from pks.settings import CRYPTOGRAPHY_KEY
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
        encrypter = Fernet(CRYPTOGRAPHY_KEY)
        token = encrypter.encrypt(raw_token.encode(encoding='utf-8'))
        # return result
        return Response({'auth_token': token}, status=status.HTTP_201_CREATED)


class VDViewset(ModelViewSet):
    queryset = models.VD.objects.all()
    serializer_class = serializers.VDSerializer
