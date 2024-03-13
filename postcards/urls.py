from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'postcards'
urlpatterns = [
    # отображение страницы  с входящими открытками
    path('', views.index, name='index'),
    path('login', views.log_in, name='login'),
    path('logout', views.log_out, name='logout'),
    # отображение страницы на добавление открытки
    path('add', login_required(views.PostcardCreateView.as_view(), login_url='/postcards/login'), name='add'),
    # отображение страницы редактирования.
    path('<int:id>/edit', views.edit, name='edit'),
    path('<int:id>/delete', views.delete, name='delete'),
    path('library', views.library, name='library'),
    path('library/add', views.library_add, name='library_add'),
    path('library/<int:id>/delete', views.library_delete, name='library_delete'),
    path('address/<int:id>/add', views.add_address, name='address_recipient'),
]
