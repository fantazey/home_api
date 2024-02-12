from django.urls import path
from . import views

app_name = 'postcards'
urlpatterns = [
    path('', views.index, name='index'),
    path('add', views.PostcardCreateView.as_view(), name='add'),
    path('<int:id>/edit', views.edit, name='edit'),
    path('<int:id>/delete', views.delete, name='delete'),
    path('library', views.library, name='library'),
    path('library/add', views.library_add, name='library_add'),
    path('library/<int:id>/delete', views.library_delete, name='library_delete'),
]