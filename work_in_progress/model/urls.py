from django.contrib.auth.decorators import login_required
from django.urls import path, reverse_lazy
from . import views

LOGIN_URL = reverse_lazy('wip:login')

app_name = 'model'
urlpatterns = [
    # model
    path('add', login_required(views.WipModelCreate.as_view(), login_url=LOGIN_URL), name='add_model'),
    path('<str:username>', views.WipUserModels.as_view(), name='models'),
    path('<int:model_id>/edit', login_required(views.WipModelUpdate.as_view(), login_url=LOGIN_URL), name='edit_model'),
    path('<int:model_id>/delete', views.delete_model, name='delete_model'),

    # progress
    path('<str:username>/<int:model_id>/progress', views.WipModelProgress.as_view(), name='progress'),
    path('<str:username>/<int:model_id>/progress/add',
         login_required(views.WipModelProgressCreate.as_view(), login_url='/wip/accounts/login'),
         name='add_progress'),
    path('<str:username>/<int:model_id>/progress/<int:progress_id>/edit',
         login_required(views.WipModelProgressUpdate.as_view(), login_url='/wip/accounts/login'),
         name='edit_progress'),
    path('<str:username>/<int:model_id>/progress/<int:progress_id>/delete',
         views.delete_progress, name='delete_progress'),

    # update status actions
    path('<str:username>/<int:model_id>/status/<str:next_status>',
         login_required(views.WipModelStatusActions.as_view(), login_url='/wip/accounts/login'),
         name='model_status_action'),
]


