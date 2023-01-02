from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.log_in, name='login'),
    path('logout', views.log_out, name='logout'),
    path('register', views.register, name='register')
]