from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('latest', views.get_last_100_measures, name='latest'),
    path('measure', views.add_measure, name='add_measure')
]