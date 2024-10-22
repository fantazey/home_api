from django.contrib import admin

# Register your models here.
from .models import Model, ModelProgress, ModelImage


class ModelAdmin(admin.ModelAdmin):
    list_filter = ['user', 'user_status']


admin.site.register(Model, ModelAdmin)


class ModelProgressAdmin(admin.ModelAdmin):
    list_filter = ['model__user', 'user_status']


admin.site.register(ModelProgress, ModelProgressAdmin)
admin.site.register(ModelImage)
