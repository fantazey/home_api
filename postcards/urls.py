from django.urls import path
from . import views

app_name = 'postcards'
urlpatterns = [
    # отображение страницы  с входящими открытками
    path('', views.index, name='index'),
    # отображение страницы на добавление открытки
    path('add', views.PostcardCreateView.as_view(), name='add'),
    # отображение страницы редактирования.
    path('<int:id>/edit', views.edit, name='edit'),
    path('<int:id>/delete', views.delete, name='delete'),
    path('library', views.library, name='library'),
    path('library/add', views.library_add, name='library_add'),
    path('library/<int:id>/delete', views.library_delete, name='library_delete'),
    path('address/<int:id>/add', views.add_address, name='address_recipient'),
]
