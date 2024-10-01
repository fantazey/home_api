from django.contrib import admin

from .models import Task, CheckList, CheckListItem, CheckListItemImage

admin.site.register(Task)
admin.site.register(CheckList)
admin.site.register(CheckListItem)
admin.site.register(CheckListItemImage)
