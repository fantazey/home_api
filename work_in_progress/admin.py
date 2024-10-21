from django.contrib import admin

# Register your models here.
from .models import Model, ModelProgress, BSUnit, BSCategory, \
    ModelImage, Artist, Paint, PaintVendor, PaintInventory, \
    KillTeam, KillTeamOperative, UserModelStatus, StatusGroup


class ModelAdmin(admin.ModelAdmin):
    list_filter = ['user', 'user_status']


admin.site.register(Model, ModelAdmin)


class ModelProgressAdmin(admin.ModelAdmin):
    list_filter = ['model__user', 'user_status']


admin.site.register(ModelProgress, ModelProgressAdmin)
admin.site.register(BSUnit)
admin.site.register(BSCategory)
admin.site.register(ModelImage)
admin.site.register(Artist)
admin.site.register(PaintVendor)
admin.site.register(PaintInventory)
admin.site.register(Paint)
admin.site.register(KillTeam)
admin.site.register(KillTeamOperative)


class UserModelStatusAdmin(admin.ModelAdmin):
    list_filter = ['user']


admin.site.register(UserModelStatus, UserModelStatusAdmin)


class StatusGroupAdmin(admin.ModelAdmin):
    list_filter = ['user']


admin.site.register(StatusGroup, StatusGroupAdmin)
