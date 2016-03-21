#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from account import models


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(username=validated_data['username'], email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()
        return user


class RealUserSerializer(ModelSerializer):
    vds = PrimaryKeyRelatedField(many=True, queryset=models.VD.objects.all())

    class Meta:
        model = models.RealUser


class VDSerializer(ModelSerializer):
    class Meta:
        model = models.VD
