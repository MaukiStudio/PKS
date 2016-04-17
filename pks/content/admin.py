from django.contrib import admin
from content import models

# Register your models here.
class LegacyPlaceAdmin(admin.ModelAdmin):
    pass

class PhoneNumberAdmin(admin.ModelAdmin):
    pass

class PlaceNameAdmin(admin.ModelAdmin):
    pass

class AddressAdmin(admin.ModelAdmin):
    pass

class PlaceNoteAdmin(admin.ModelAdmin):
    pass

class ImageNoteAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.LegacyPlace, LegacyPlaceAdmin)
admin.site.register(models.PhoneNumber, PhoneNumberAdmin)
admin.site.register(models.PlaceName, PlaceNameAdmin)
admin.site.register(models.Address, AddressAdmin)
admin.site.register(models.PlaceNote, PlaceNoteAdmin)
admin.site.register(models.ImageNote, ImageNoteAdmin)
