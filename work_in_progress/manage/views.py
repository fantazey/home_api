from django.shortcuts import  redirect
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import FormView

from work_in_progress.models import Artist
from .forms import UserSettingsForm
from .models import UserModelStatus


class WipManageSettings(FormView):
    model = Artist
    form_class = UserSettingsForm
    template_name = 'wip/manage/user_settings.html'

    def get_initial(self):
        artist = Artist.objects.get(user=self.request.user)
        return {
            'telegram_name': artist.telegram_name
        }

    def form_valid(self, form):
        artist = Artist.objects.get(user=self.request.user)
        artist.telegram_name = form.cleaned_data['telegram_name']
        artist.save()
        return redirect(reverse('wip:manage'))


class WipManageUserModelStatus(ListView):
    model = UserModelStatus
    template_name = 'wip/manage/user_model_status_list.html'
    context_object_name = 'user_model_statuses'

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)
