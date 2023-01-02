from django.urls import path

from . import views

app_name = 'wip'
urlpatterns = [
    path('', views.index, name='index'),
    path('add', views.add_model, name='add_model'),
    path('login', views.log_in, name='login'),
    path('logout', views.log_out, name='logout'),
    path('register', views.register, name='register'),
]