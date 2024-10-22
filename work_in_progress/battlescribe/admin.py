from django.contrib import admin

# Register your models here.
from .models import BSUnit, BSCategory, KillTeam, KillTeamOperative

admin.site.register(BSUnit)
admin.site.register(BSCategory)
admin.site.register(KillTeam)
admin.site.register(KillTeamOperative)


