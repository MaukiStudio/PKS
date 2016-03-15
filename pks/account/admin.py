#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis import admin
from .models import VD

admin.site.register(VD, admin.OSMGeoAdmin)

