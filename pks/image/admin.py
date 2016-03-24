from django.contrib import admin
from image import models

# Register your models here.
class ImageAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Image, ImageAdmin)
