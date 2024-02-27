from django.contrib import admin

# Register your models here.
from .models import Model, ModelProgress, BSUnit, BSCategory, \
    ModelImage, Artist, Paint, PaintVendor, PaintInventory, \
    KillTeam, KillTeamOperative

admin.site.register(Model)
admin.site.register(ModelProgress)
admin.site.register(BSUnit)
admin.site.register(BSCategory)
admin.site.register(ModelImage)
admin.site.register(Artist)
admin.site.register(PaintVendor)
admin.site.register(PaintInventory)
admin.site.register(Paint)
admin.site.register(KillTeam)
admin.site.register(KillTeamOperative)