from django.contrib.auth.decorators import login_required
from django.urls import path, reverse_lazy
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
    # inventory
    path('inventory',
         login_required(views.WipUserInventory.as_view(), login_url='/wip/accounts/login'),
         name='inventory'),
    path('inventory/manage',
         login_required(views.WipUserInventoryManage.as_view(), login_url='/wip/accounts/login'),
         name='inventory_manage'),
    # model
    path('<str:username>/model', views.WipUserModels.as_view(), name='models'),
    path('model/add',
         login_required(views.WipModelCreate.as_view(), login_url=LOGIN_URL),
         name='add_model'),
    path('model/<int:model_id>/edit',
         login_required(views.WipModelUpdate.as_view(), login_url=LOGIN_URL),
         name='edit_model'),
    path('model/<int:model_id>/delete', views.delete_model, name='delete_model'),

    # progress
    path('<str:username>/model/<int:model_id>/progress', views.WipModelProgress.as_view(), name='progress'),
    path('<str:username>/model/<int:model_id>/progress/add',
         login_required(views.WipModelProgressCreate.as_view(), login_url='/wip/accounts/login'),
         name='add_progress'),
    path('<str:username>/model/<int:model_id>/progress/<int:progress_id>/edit',
         login_required(views.WipModelProgressUpdate.as_view(), login_url='/wip/accounts/login'),
         name='edit_progress'),
    path('<str:username>/model/<int:model_id>/progress/<int:progress_id>/delete',
         views.delete_progress, name='delete_progress'),

    # update status actions
    path('<str:username>/model/<int:model_id>/<str:status_action>',
         login_required(views.WipModelStatusActions.as_view(), login_url='/wip/accounts/login'),
         name='model_status_action'),
]

