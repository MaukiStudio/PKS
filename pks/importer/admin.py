from django.contrib import admin
from importer.models import Proxy, Importer


# Register your models here.
class ProxyAdmin(admin.ModelAdmin):
    pass

class ImporterAdmin(admin.ModelAdmin):
    pass


admin.site.register(Proxy, ProxyAdmin)
admin.site.register(Importer, ImporterAdmin)
