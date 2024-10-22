from django.urls import path, reverse_lazy, include
from . import views

LOGIN_URL = reverse_lazy('wip:login')

app_name = 'wip'
urlpatterns = [
    # common paths
    path('accounts/login/', views.WipLoginView.as_view(), name='login'),
    path('accounts/logout', views.log_out, name='logout'),
    path('accounts/register', views.WipRegisterView.as_view(), name='register'),
    path('about', views.about, name='about'),

    # index
    path('', views.WipIndexView.as_view(), name='index'),

    # manage
    path('manage/', include('work_in_progress.manage.urls')),

    # inventory
    path('inventory/', include('work_in_progress.inventory.urls')),

    # model
    path('models/', include('work_in_progress.model.urls')),
]

