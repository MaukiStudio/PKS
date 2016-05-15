#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis import admin
from account.models import VD, User, RealUser


class VDAdmin(admin.OSMGeoAdmin):
    pass

class UserAdmin(admin.ModelAdmin):
    pass

class RealUserAdmin(admin.ModelAdmin):
    pass

admin.site.register(VD, VDAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(RealUser, RealUserAdmin)
