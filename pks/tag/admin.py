#-*- coding: utf-8 -*-
from django.contrib import admin
from tag.models import Tag, UserPlaceTag, PlaceTag


# Register your models here.
class TagAdmin(admin.ModelAdmin):
    pass

class UserPlaceTagAdmin(admin.ModelAdmin):
    pass

class PlaceTagAdmin(admin.ModelAdmin):
    pass


admin.site.register(Tag, TagAdmin)
admin.site.register(UserPlaceTag, UserPlaceTagAdmin)
admin.site.register(PlaceTag, PlaceTagAdmin)
