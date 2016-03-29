from django.contrib import admin
from url import models

# Register your models here.
class UrlAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Url, UrlAdmin)
