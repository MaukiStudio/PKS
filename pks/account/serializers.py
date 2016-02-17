#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User

from rest_framework.serializers import HyperlinkedModelSerializer

from account import models


class UserSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = User

class VDSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = models.VD
