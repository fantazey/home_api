import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max, Sum, Q
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, View
from django.views.generic.edit import FormView

from .forms import AddModelForm, AddProgressForm, EditModelForm, ModelFilterForm, WorkMapFilterForm
from .models import Model, ModelProgress, ModelImage, UserModelStatus
from work_in_progress.manage.models import StatusGroup


class WipUserModels(ListView):
    model = Model
    template_name = 'wip/model/model/list.html'
    context_object_name = 'models'

    def get_paginate_by(self, queryset):
        return self.request.GET.get('page_size', 12)

    def get_queryset(self):
        user = self.get_user()
        old_date = timezone.now() - datetime.timedelta(days=2000)
        user_models = Model.objects.annotate(last_record=Max('progress__datetime', default=old_date)) \
            .filter(user=user) \
            .order_by('-last_record', 'buy_date', 'created')
        form = self.get_filter_form(user)
        if form.is_valid():
            if form.cleaned_data['status']:
                user_models = user_models.filter(user_status=form.cleaned_data['status'])
        if self.request.user != user:
            user_models = user_models.filter(hidden=False)
        return user_models

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user = self.get_user()

        map_filter_year = datetime.date.today().year
        map_filter_form = self.get_work_map_filter_form()
        if map_filter_form.is_valid():
            map_filter_year = map_filter_form.cleaned_data['work_map_year']
        progress_list = ModelProgress.objects.filter(model__user=user, time__gt=0) \
            .filter(datetime__year=map_filter_year)
        progress_by_date = {}
        for progress in progress_list:
            d = timezone.localtime(progress.datetime).date().strftime("%d-%m-%Y")
            if d not in progress_by_date.keys():
                progress_by_date[d] = 0
            progress_by_date[d] += progress.time

        date_map = build_map(progress_by_date, map_filter_year)
        sum_time_by_status = progress_list.filter(Q(user_status__isnull=False)) \
            .values("user_status__name") \
            .annotate(total_time=Sum('time'))\
            .order_by("user_status__order")
        sum_time_by_sorted_status = sum_time_by_status

        user_models = Model.objects.filter(user=user)
        status_groups = StatusGroup.objects.filter(user=user)
        units_count_by_status_group = {}
        for status_group in status_groups:
            query = Q(user_status__group=status_group) & Q(terrain=False)
            terrain_query = Q(user_status__group=status_group) & Q(terrain=True)
            units_count_by_status_group[status_group.name] = {
                'model': user_models.filter(query).aggregate(Sum('unit_count'))['unit_count__sum'],
                'terrain': user_models.filter(terrain_query).aggregate(Sum('unit_count'))['unit_count__sum']
            }
        units_total = user_models.filter(Q(terrain=False)).aggregate(Sum('unit_count'))['unit_count__sum']
        terrain_total = user_models.filter(Q(terrain=True)).aggregate(Sum('unit_count'))['unit_count__sum']
        status_map = [(x['user_status__name'], x['total_time']) for x in sum_time_by_sorted_status]
        status_map.append(('Итого', sum_time_by_status.aggregate(Sum('total_time'))['total_time__sum']))
        status_map = [status_map[:5], status_map[5:]]
        return context | {
            'user': user,
            'filter_form': self.get_filter_form(user),
            'work_map_filter_form': map_filter_form,
            'date_map': date_map,
            'time_status_map': status_map,
            'units_count_by_status_group': units_count_by_status_group,
            'units_total': units_total,
            'terrain_total': terrain_total
        }

    def get_user(self) -> User:
        users = User.objects.filter(username=self.kwargs['username'])
        if not users.exists():
            raise Http404("Пользователь не найден")
        return users.first()

    def get_filter_form(self, user: User):
        # todo: добавить фильтр по террейн/киллтим/категория battlescribe
        return ModelFilterForm(self.request.GET, user=user)

    def get_work_map_filter_form(self):
        return WorkMapFilterForm(self.request.GET, initial={'work_map_year': datetime.date.today().year})


def build_map(progress_by_date, year):
    start = datetime.date(year, 1, 1)
    end = datetime.date(year, 12, 31)
    date_map = []
    week = [(-50, -50, 0,)] * 7
    current_date = start
    week_num = 0
    keys = progress_by_date.keys()
    while current_date <= end:
        date_str = current_date.strftime('%d-%m-%Y')
        wd = current_date.weekday()
        x = (week_num * 10) + (week_num + 1) * 2
        y = (wd * 10) + (wd + 1) * 2
        value = progress_by_date[date_str] if date_str in keys else 0
        week[wd] = (x, y, value, current_date.day, x + 5, y + 8)
        if wd == 6:
            date_map.append(week)
            week_num += 1
            week = [None] * 7
        current_date = current_date + datetime.timedelta(days=1)
    return date_map


class WipModelCreate(FormView):
    form_class = AddModelForm
    template_name = 'wip/model/model/add.html'

    def get_form_kwargs(self):
        parent_kwargs = super().get_form_kwargs()
        parent_kwargs['user'] = self.request.user
        return parent_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление модели в PileOfShame'
        context['submit_url'] = reverse('wip:model:add_model')
        context['submit_label'] = 'Добавить'
        return context

    def form_valid(self, form):
        name = form.cleaned_data['name']
        status = UserModelStatus.objects.get(user=self.request.user, is_initial=True)
        model = Model(name=name,
                      user=self.request.user,
                      user_status=status,
                      battlescribe_unit=form.cleaned_data['bs_unit'],
                      buy_date=form.cleaned_data['buy_date'],
                      kill_team=form.cleaned_data['bs_kill_team'],
                      hidden=form.cleaned_data['hidden'],
                      unit_count=form.cleaned_data['count'])
        progress_title = "Захотелось новую модельку"
        if form.cleaned_data['status']:
            model.user_status = form.cleaned_data['status']
            progress_title = form.cleaned_data['status'].transition_title

        model.save()
        progress = ModelProgress(datetime=datetime.datetime.now(), title=progress_title, model=model,
                                 user_status=model.user_status)
        progress.save()
        return redirect(reverse('wip:model:models', kwargs={'username': self.request.user.username}))


class WipModelUpdate(FormView):
    form_class = EditModelForm
    template_name = 'wip/model/model/edit.html'

    def get_form_kwargs(self):
        parent_kwargs = super().get_form_kwargs()
        parent_kwargs['user'] = self.request.user
        return parent_kwargs

    def get_model(self) -> Model:
        return Model.objects.get(id=self.kwargs['model_id'], user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model = self.get_model()
        context['title'] = 'Редактирование модели %s' % model
        context['submit_url'] = reverse('wip:model:edit_model', kwargs={'model_id': self.kwargs['model_id']})
        context['submit_label'] = 'Сохранить'
        return context

    def get_initial(self):
        model = self.get_model()
        initial = {
            'name': model.name,
            'buy_date': model.buy_date.strftime('%Y-%m-%d') if model.buy_date is not None else None,
            'bs_unit': model.battlescribe_unit,
            'status': model.user_status,
            'bs_category': model.battlescribe_unit.bs_category if model.battlescribe_unit is not None else None,
            'bs_kill_team': model.kill_team,
            'hidden': model.hidden,
            'count': model.unit_count
        }
        return initial

    def form_valid(self, form):
        model = self.get_model()
        model.name = form.cleaned_data['name']
        model.battlescribe_unit = form.cleaned_data['bs_unit']
        model.kill_team = form.cleaned_data['bs_kill_team']
        model.buy_date = form.cleaned_data['buy_date']
        if model.user_status != form.cleaned_data['status']:
            progress = ModelProgress(model=model,
                                     title="Смена статуса на: %s" % Model.Status(form.cleaned_data['status']).label,
                                     time=0,
                                     user_status=model.user_status,
                                     datetime=datetime.datetime.now())
            progress.save()
        model.user_status = form.cleaned_data['status']
        model.hidden = form.cleaned_data['hidden']
        model.unit_count = form.cleaned_data['count']
        model.save()
        return redirect(reverse('wip:model:models', kwargs={'username': self.request.user.username}))


@login_required(login_url='/wip/accounts/login')
def delete_model(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model_progress = ModelProgress.objects.filter(model=model)
    model_progress.delete()
    model_images = ModelImage.objects.filter(model=model)
    model_images.delete()
    model.delete()
    return redirect(reverse('wip:model:models', kwargs={'username': request.user.username}))


class WipModelProgress(ListView):
    model = ModelProgress
    context_object_name = 'progress_items'
    template_name = 'wip/model/progress/list.html'

    def get_user(self):
        users = User.objects.filter(username=self.kwargs['username'])
        if not users.exists():
            return Http404("Пользователь не найден")
        return users.first()

    def get_model(self):
        user = self.get_user()
        return Model.objects.get(id=self.kwargs['model_id'], user=user)

    def get_queryset(self):
        progress_items = ModelProgress.objects.filter(model=self.get_model()).order_by('-datetime')
        return progress_items

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['total'] = context['progress_items'].aggregate(Sum('time'))['time__sum']
        context['model'] = self.get_model()
        context['user'] = self.get_user()
        return context


class WipModelProgressCreate(FormView):
    template_name = 'wip/model/progress/form.html'
    form_class = AddProgressForm

    def get_form_kwargs(self):
        parent_kwargs = super().get_form_kwargs()
        parent_kwargs['user'] = self.get_user()
        return parent_kwargs

    def get_user(self):
        return self.request.user

    def get_model(self) -> Model:
        return Model.objects.get(id=self.kwargs['model_id'], user=self.get_user())

    def get_context_data(self, **kwargs):
        model = self.get_model()
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление прогресса для модели %s' % model
        context['model'] = model
        context['submit_url'] = reverse('wip:model:add_progress', kwargs={
            'username': self.get_user().username,
            'model_id': model.id})
        context['submit_label'] = 'Добавить'
        return context

    def get_initial(self):
        return {'status': self.get_model().user_status}

    def form_valid(self, form):
        model = self.get_model()
        progress = ModelProgress(model=model,
                                 title=form.cleaned_data['title'],
                                 description=form.cleaned_data['description'],
                                 time=form.cleaned_data['time'],
                                 user_status=form.cleaned_data['status'],
                                 datetime=form.cleaned_data['date'])
        progress.save()
        progress.add_images(self.request.FILES.getlist('images'))
        return redirect(reverse('wip:model:progress', args=(model.user.username, model.id,)))


class WipModelProgressUpdate(WipModelProgressCreate):

    def get_progress(self):
        return ModelProgress.objects.get(id=self.kwargs['progress_id'], model=self.get_model())

    def get_initial(self):
        initial = super().get_initial()
        progress = self.get_progress()
        return initial | {
            'title': progress.title,
            'description': progress.description,
            'date': progress.datetime,
            'time': progress.time,
            'status': progress.user_status,
            'images': progress.modelimage_set.values('image')
        }

    def get_context_data(self, **kwargs):
        model = self.get_model()
        progress = self.get_progress()
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование записи покраса %s для модели %s' % (progress, model)
        context['submit_label'] = 'Сохранить'
        context['submit_url'] = reverse('wip:model:edit_progress', kwargs={
            'username': self.request.user.username,
            'model_id': model.id,
            'progress_id': progress.id})
        return context

    def form_valid(self, form):
        model = self.get_model()
        progress = self.get_progress()
        progress.title = form.cleaned_data['title']
        progress.description = form.cleaned_data['description']
        progress.time = form.cleaned_data['time']
        progress.datetime = form.cleaned_data['date']
        progress.user_status = form.cleaned_data['status']
        progress.save()
        progress.add_images(self.request.FILES.getlist('images'))
        return redirect(reverse('wip:model:progress', args=(model.user.username, model.id,)))


@login_required(login_url='/wip/accounts/login')
def delete_progress(request, username, model_id, progress_id):
    model = Model.objects.get(id=model_id, user=request.user)
    progress = ModelProgress.objects.get(id=progress_id, model=model)
    images = ModelImage.objects.filter(progress=progress)
    images.delete()
    model = progress.model
    progress.delete()
    return redirect(reverse('wip:model:progress', args=(model.user.username, model.id,)))


class WipModelStatusActions(View):
    def get_model(self) -> Model:
        return Model.objects.get(id=self.kwargs['model_id'], user=self.request.user)

    def get(self, *args, **kwargs):
        self.get_model().change_status(self.kwargs['next_status'])
        return redirect(reverse('wip:model:models', kwargs={'username': self.request.user.username}))
