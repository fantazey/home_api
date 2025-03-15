from django.contrib.auth.decorators import login_required
from django.urls import path, reverse_lazy, include

# from rest_framework import routers
from rest_framework_nested import routers
from knox import views as knox_views

from . import views

LOGIN_URL = reverse_lazy('wip:login')

router = routers.DefaultRouter()
router.register(r"models", views.ApiWipModelsViewSet)
models_router = routers.NestedDefaultRouter(router, r'models', lookup='model')
models_router.register(r'progress', views.ApiWipModelProgressViewSet, basename='models-progress')
models_router.register(r'images', views.ApiWipModelImagesViewSet, basename='models-images')

router.register(r"statuses", views.ApiWipUserModelStatusesViewSet)
router.register(r"model-groups", views.ApiWipModelGroupViewSet)
router.register(r"bs-categories", views.ApiWipBattleScribeCategoryViewSet)
router.register(r"bs-units", views.ApiWipBattleScribeUnitsViewSet)
router.register(r"kill-teams", views.ApiWipKillTeamViewSet)

app_name = 'wip'
urlpatterns = [
    # api
    path('api/auth/login/', views.ApiWipLoginView.as_view(), name='knox_login'),
    path('api/auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('api/auth/logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
    path('api/', include(router.urls)),
    path('api/', include(models_router.urls)),

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
    # manage
    path('manage',
         login_required(views.manage, login_url='/wip/accounts/login'),
         name='manage'),
    # manage status_group
    path('manage/status_group/list',
         login_required(views.WipUserStatusGroupManage.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_group_list'),
    path('manage/status_group/add',
         login_required(views.WipUserStatusGroupManageCreate.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_group_add'),
    path('manage/status_group/<int:status_group_id>/edit',
         login_required(views.WipUserStatusGroupManageUpdate.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_group_edit'),
    path('manage/status_group/<int:status_group_id>/delete',
         login_required(views.delete_user_status_group, login_url='/wip/accounts/login'),
         name='manage_status_group_delete'),

    # manage status
    path('manage/status/list',
         login_required(views.WipUserStatusManage.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_list'),
    path('manage/status/add',
         login_required(views.WipUserStatusManageCreate.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_add'),
    path('manage/status/<int:status_id>/edit',
         login_required(views.WipUserStatusManageUpdate.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_edit'),
    path('manage/status/<int:status_id>/delete',
         login_required(views.delete_user_status, login_url='/wip/accounts/login'),
         name='manage_status_delete'),

    # manage model group
    path('manage/model_group/list',
         login_required(views.WipUserModelGroupManage.as_view(), login_url='/wip/accounts/login'),
         name='manage_model_group_list'),
    path('manage/model_group/add',
         login_required(views.WipUserModelGroupManageCreate.as_view(), login_url='/wip/accounts/login'),
         name='manage_model_group_add'),
    path('manage/model_group/<int:model_group_id>/edit',
         login_required(views.WipUserModelGroupManageUpdate.as_view(), login_url='/wip/accounts/login'),
         name='manage_model_group_edit'),
    path('manage/model_group/<int:model_group_id>/delete',
         login_required(views.delete_user_model_group, login_url='/wip/accounts/login'),
         name='manage_model_group_delete'),

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
    path('<str:username>/model/<int:model_id>/<str:next_status>',
         login_required(views.WipModelStatusActions.as_view(), login_url='/wip/accounts/login'),
         name='model_status_action'),
]

