from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'postcards'
urlpatterns = [
    path('login', views.log_in, name='login'),
    path('logout', views.log_out, name='logout'),

    # отображение страницы редактирования.
    path('', views.PostcardsListView.as_view(), name='index'),
    # отображение страницы на добавление открытки
    path('add', login_required(views.PostcardCreateView.as_view(), login_url='/postcards/login'), name='add'),
    path('<int:id>/edit', login_required(views.PostcardEditView.as_view(), login_url='/postcards/login'), name='edit'),
    path('<int:id>/delete', login_required(views.PostcardDeleteView.as_view(), login_url='/postcards/login'),
         name='delete'),
    path('library', views.LibraryListView.as_view(), name='library'),
    path('library/add', views.library_add, name='library_add'),
    path('library/<int:id>/delete', views.library_delete, name='library_delete'),
    path('address/<int:id>/add', views.add_address, name='address_recipient'),
]
