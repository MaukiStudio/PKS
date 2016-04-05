from django.contrib import admin
from content import models

# Register your models here.
class LegacyPlaceAdmin(admin.ModelAdmin):
    pass

class ShortTextAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.LegacyPlace, LegacyPlaceAdmin)
admin.site.register(models.ShortText, ShortTextAdmin)
