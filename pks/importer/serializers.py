#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.serializers import BaseSerializer
from importer.models import Proxy, Importer


class ProxySerializer(BaseSerializer):
    class Meta:
        model = Proxy


class ImporterSerializer(BaseSerializer):
    class Meta:
        model = Importer
