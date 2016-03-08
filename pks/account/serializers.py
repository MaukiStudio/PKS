#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid1
from django.contrib.auth.models import User
from rest_framework.serializers import HyperlinkedModelSerializer

from cryptography.fernet import Fernet
from account import models


class UserSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        username = validated_data['username'] or uuid1()
        password = validated_data['password'] or User.objects.make_random_password()
        user = User(
            username=username
        )
        user.set_password(password)
        user.save()
        return user


class VDSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = models.VD
