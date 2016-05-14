#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from image.models import Image, RawFile
from base.serializers import ContentSerializer


class ImageSerializer(ContentSerializer):
    class Meta:
        model = Image
        exclude = ('id', 'dhash',)


class RawFileSerializer(ModelSerializer):
    uuid = ReadOnlyField()
    url = ReadOnlyField()

    class Meta:
        model = RawFile
        exclude = ('id', 'mhash',)
        # TODO : 하위 호환을 위한 임시 주석 처리. 훈자 작업 완료 후 주석 해제
        #extra_kwargs = {'file': {'write_only': True}}
