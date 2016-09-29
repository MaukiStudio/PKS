#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from etc.models import Notice, Inquiry
from etc.serializers import NoticeSerializer, InquirySerializer
from base.views import BaseViewset


class NoticeViewset(BaseViewset):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer


class InquiryViewset(BaseViewset):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer

    def perform_create(self, serializer):
        serializer.save(ru=self.vd.realOwner)

    def get_queryset(self):
        return self.vd.realOwner.inquiries.order_by('-id')
