import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db.models import Max
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic.edit import FormView

from work_in_progress.forms import LoginForm, RegistrationForm
from work_in_progress.model.models import Model
from work_in_progress.models import Artist


class WipLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "wip/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse('wip:model', kwargs={'username': self.request.user.username})


class WipRegisterView(FormView):
    model = Artist
    form_class = RegistrationForm
    template_name = 'wip/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('wip:index'))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('wip:model', kwargs={'username': self.request.user.username})

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        first_name = form.cleaned_data['first_name']
        telegram_name = form.cleaned_data['telegram_name']
        if User.objects.filter(username=username).exists():
            form.add_error('username', 'Пользователь существует')
            return render(self.request, 'wip/register.html', {'form': form}, status=400)

        user = User(username=username, first_name=first_name)
        user.set_password(password)
        user.save()
        artist = Artist(user=user, telegram_name=telegram_name)
        artist.save()
        user = authenticate(self.request, username=username, password=password)
        if user is None:
            form.add_error('username', 'ошибка при создании пользователя')
            return render(self.request, 'wip/register.html', {'form': form}, status=400)

        login(self.request, user)
        return redirect(reverse('wip:index'))


@login_required(login_url='/wip/accounts/login')
def log_out(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse('wip:login'))


def about(request):
    return render(request, 'wip/about.html')


class WipIndexView(ListView):
    model = Model
    paginate_by = 20
    template_name = 'wip/index.html'
    context_object_name = 'models'

    def get_queryset(self):
        old_date = timezone.now() - datetime.timedelta(days=2000)
        return Model.objects.annotate(last_record=Max('progress__datetime', default=old_date)). \
            filter(hidden=False). \
            order_by('-last_record')


