#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ReadOnlyField

from base.serializers import BaseSerializer
from etc.models import Notice, Inquiry


class NoticeSerializer(BaseSerializer):
    created = ReadOnlyField()

    class Meta:
        model = Notice


class InquirySerializer(BaseSerializer):
    created = ReadOnlyField()
    ru = ReadOnlyField(source='ru_id')

    class Meta:
        model = Inquiry
