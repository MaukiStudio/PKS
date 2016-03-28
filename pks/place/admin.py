from django.contrib import admin
from place import models

# Register your models here.
class PlaceAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Place, PlaceAdmin)
