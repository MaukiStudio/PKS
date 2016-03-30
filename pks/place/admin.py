from django.contrib import admin
from place import models

# Register your models here.
class PlaceAdmin(admin.ModelAdmin):
    pass

class PlaceContentAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Place, PlaceAdmin)
admin.site.register(models.PlaceContent, PlaceContentAdmin)
