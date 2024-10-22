from django.contrib import admin

from .models import Paint, PaintVendor, PaintInventory

admin.site.register(PaintVendor)
admin.site.register(PaintInventory)
admin.site.register(Paint)