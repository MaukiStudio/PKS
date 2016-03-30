from django.contrib import admin
from content import models

# Register your models here.
class FsVenueAdmin(admin.ModelAdmin):
    pass

class NoteAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.FsVenue, FsVenueAdmin)
admin.site.register(models.Note, NoteAdmin)
