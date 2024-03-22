from django.contrib import admin

from .models import Postcard, Library, Address

admin.site.register(Postcard)
admin.site.register(Library)
admin.site.register(Address)
