#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework.serializers import ModelSerializer

from account import models


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(username=validated_data['username'])
        user.set_password(validated_data['password'])
        user.save()
        return user


class RealUserSerializer(ModelSerializer):
    class Meta:
        model = models.RealUser


class VDSerializer(ModelSerializer):
    class Meta:
        model = models.VD
