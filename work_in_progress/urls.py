from django.urls import path
from . import views

app_name = 'wip'
urlpatterns = [
    # common paths
    path('accounts/login/', views.log_in, name='login'),
    path('accounts/logout', views.log_out, name='logout'),
    path('accounts/register', views.register, name='register'),
    path('about', views.about, name='about'),

    path('add', views.add_model, name='add_model'),
    path('<int:model_id>/edit', views.edit_model, name='edit_model'),
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
    # progress

    path('<int:model_id>/track', views.track_progress, name='track_progress'),

    path('', views.index, name='index'),
    path('<str:username>', views.models, name='models'),
    path('<str:username>/<int:model_id>/progress', views.view_progress, name='progress'),
]

