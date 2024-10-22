from django.contrib import admin

# Register your models here.
from .models import UserModelStatus, StatusGroup


class UserModelStatusAdmin(admin.ModelAdmin):
    list_filter = ['user']


admin.site.register(UserModelStatus, UserModelStatusAdmin)


class StatusGroupAdmin(admin.ModelAdmin):
    list_filter = ['user']


admin.site.register(StatusGroup, StatusGroupAdmin)
