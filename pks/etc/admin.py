from django.contrib import admin
from etc import models

# Register your models here.
class NoticeAdmin(admin.ModelAdmin):
    pass

class InquiryAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Notice, NoticeAdmin)
admin.site.register(models.Inquiry, InquiryAdmin)
