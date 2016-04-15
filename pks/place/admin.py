from django.contrib import admin
from place.models import Place, UserPlace, PostPiece

# Register your models here.
class PlaceAdmin(admin.ModelAdmin):
    pass

class UserPlaceAdmin(admin.ModelAdmin):
    pass

class PostPieceAdmin(admin.ModelAdmin):
    pass


admin.site.register(Place, PlaceAdmin)
admin.site.register(UserPlace, UserPlaceAdmin)
admin.site.register(PostPiece, PostPieceAdmin)
