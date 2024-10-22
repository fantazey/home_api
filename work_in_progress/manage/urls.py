from django.contrib.auth.decorators import login_required
from django.urls import path, reverse_lazy
from . import views

LOGIN_URL = reverse_lazy('wip:login')
app_name = 'manage'
urlpatterns = [
    # manage
    path('manage',
         login_required(views.WipManageSettings.as_view(), login_url='/wip/accounts/login'),
         name='manage'),
    path('manage/status',
         login_required(views.WipManageUserModelStatus.as_view(), login_url='/wip/accounts/login'),
         name='manage_status'),
    path('manage/status/add',
         login_required(views.WipManageUserModelStatus.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_edit'),
    path('manage/status/<int:status_id>/edit',
         login_required(views.WipManageUserModelStatus.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_edit'),
    path('manage/status-groups',
         login_required(views.WipManageSettings.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_groups'),
    path('manage/status-groups/<int:group_id>/edit',
         login_required(views.WipManageSettings.as_view(), login_url='/wip/accounts/login'),
         name='manage_status_groups_edit'),
]

