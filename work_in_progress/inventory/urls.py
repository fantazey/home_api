from django.contrib.auth.decorators import login_required
from django.urls import path, reverse_lazy
from . import views

LOGIN_URL = reverse_lazy('wip:login')

app_name = 'inventory'
urlpatterns = [
    # inventory
    path('',
         login_required(views.WipUserInventory.as_view(), login_url='/wip/accounts/login'),
         name='inventory'),
    path('manage',
         login_required(views.WipUserInventoryManage.as_view(), login_url='/wip/accounts/login'),
         name='inventory_manage')
]

