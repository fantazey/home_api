from django.urls import path
from . import views

app_name = 'wip'
urlpatterns = [
    # common paths
    path('accounts/login/', views.WipLoginView.as_view(), name='login'),
    path('accounts/logout', views.log_out, name='logout'),
    path('accounts/register', views.WipRegisterView.as_view(), name='register'),
    path('about', views.about, name='about'),

    # update status actions
    path('<int:model_id>/put_in_inventory', views.put_in_inventory, name='put_in_inventory'),
    path('<int:model_id>/start_assembly', views.start_assembly, name='start_assembly'),
    path('<int:model_id>/finish_assembly', views.finish_assembly, name='finish_assembly'),
    path('<int:model_id>/start_priming', views.start_priming, name='start_priming'),
    path('<int:model_id>/finish_priming', views.finish_priming, name='finish_priming'),
    path('<int:model_id>/start_painting', views.start_painting, name='start_painting'),
    path('<int:model_id>/finish_painting', views.finish_painting, name='finish_painting'),
    path('<int:model_id>/start_parade_ready_painting', views.start_parade_ready_painting,
         name='start_parade_ready_painting'),
    path('<int:model_id>/finish_parade_ready_painting', views.finish_parade_ready_painting,
         name='finish_parade_ready_painting'),
    path('<int:model_id>/start_base_decoration', views.start_base_decoration, name='start_base_decoration'),
    path('<int:model_id>/finish_base_decoration', views.finish_base_decoration, name='finish_base_decoration'),
    path('<int:model_id>/start_varnishing', views.start_varnishing, name='start_varnishing'),
    path('<int:model_id>/finish_varnishing', views.finish_varnishing, name='finish_varnishing'),

    # index
    path('', views.WipIndexView.as_view(), name='index'),
    # model
    path('<str:username>/model', views.WipUserModels.as_view(), name='models'),
    path('model/add', views.add_model, name='add_model'),
    path('model/<int:model_id>/edit', views.edit_model, name='edit_model'),
    path('model/<int:model_id>/delete', views.delete_model, name='delete_model'),

    # progress
    path('<str:username>/model/<int:model_id>/progress', views.view_progress, name='progress'),
    path('model/<int:model_id>/progress/add', views.add_progress, name='add_progress'),
    path('model/<int:model_id>/progress/<int:progress_id>/edit',
         views.edit_progress, name='edit_progress'),
    path('model/<int:model_id>/progress/<int:progress_id>/delete',
         views.delete_progress, name='delete_progress'),
]

