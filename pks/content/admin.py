from django.contrib import admin
from content import models

# Register your models here.
class FsVenueAdmin(admin.ModelAdmin):
    pass

class ShortTextAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.FsVenue, FsVenueAdmin)
admin.site.register(models.ShortText, ShortTextAdmin)
