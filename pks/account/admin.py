#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis import admin
from account import models

class UserAdmin(admin.ModelAdmin):
    pass

class RealUserAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.VD, admin.OSMGeoAdmin)
admin.site.register(models.User, UserAdmin)
admin.site.register(models.RealUser, RealUserAdmin)
