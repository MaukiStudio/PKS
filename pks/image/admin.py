from django.contrib import admin
from image import models

# Register your models here.
class ImageAdmin(admin.ModelAdmin):
    pass

class RawFileAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Image, ImageAdmin)
admin.site.register(models.RawFile, RawFileAdmin)
