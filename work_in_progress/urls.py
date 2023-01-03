from django.urls import path

from . import views

app_name = 'wip'
urlpatterns = [
    path('', views.index, name='index'),
    path('add', views.add_model, name='add_model'),
    path('in_inventory', views.add_model, name='in_inventory'),
    path('<int:model_id>', views.view_progress, name='view_model'),
    path('<int:model_id>/add', views.add_progress, name='add_progress'),
    path('login', views.log_in, name='login'),
    path('logout', views.log_out, name='logout'),
    path('register', views.register, name='register'),
]