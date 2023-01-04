from django.urls import path

from . import views

app_name = 'wip'
urlpatterns = [
    path('', views.index, name='index'),
    path('add', views.add_model, name='add_model'),
    path('<int:model_id>/put_in_inventory', views.put_in_inventory, name='put_in_inventory'),
    path('<int:model_id>/progress', views.view_progress, name='progress'),
    path('<int:model_id>/track', views.track_progress, name='track_progress'),


    path('login', views.log_in, name='login'),
    path('logout', views.log_out, name='logout'),
    path('register', views.register, name='register'),
]
