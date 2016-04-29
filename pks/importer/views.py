#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.views import BaseViewset
from importer.models import Proxy, Importer
from importer.serializers import ProxySerializer, ImporterSerializer


class ProxyViewset(BaseViewset):
    queryset = Proxy.objects.all()
    serializer_class = ProxySerializer


class ImporterViewset(BaseViewset):
    queryset = Importer.objects.all()
    serializer_class = ImporterSerializer

