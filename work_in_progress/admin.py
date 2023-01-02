from django.contrib import admin

# Register your models here.
from .models import Model, ModelProgress

admin.site.register(Model)
admin.site.register(ModelProgress)