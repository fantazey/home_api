import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db.models import Max, Sum, Q
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, View
from django.views.generic.edit import FormView

from rest_framework import viewsets, permissions, generics, authentication

from .forms import AddModelForm, LoginForm, AddProgressForm, RegistrationForm, EditModelForm, \
    ModelFilterForm, WorkMapFilterForm, PaintInventoryManageForm, InventoryFilterForm, StatusGroupForm, \
    UserStatusForm, ModelGroupForm
from .models import Model, ModelProgress, ModelImage, Artist, PaintInventory, Paint, PaintVendor, UserModelStatus, \
    StatusGroup, ModelGroup
from .serializers import ModelSerializer, UserModelStatusSerializer


class WipLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "wip/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse('wip:models', kwargs={'username': self.request.user.username})


class WipRegisterView(FormView):
    model = Artist
    form_class = RegistrationForm
    template_name = 'wip/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('wip:index'))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('wip:models', kwargs={'username': self.request.user.username})

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


class WipUserModels(ListView):
    model = Model
    template_name = 'wip/models.html'
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
            if form.cleaned_data['group']:
                user_models = user_models.filter(groups__in=[form.cleaned_data['group']])
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
    template_name = 'wip/model_add.html'

    def get_form_kwargs(self):
        parent_kwargs = super().get_form_kwargs()
        parent_kwargs['user'] = self.request.user
        return parent_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление модели в PileOfShame'
        context['submit_url'] = reverse('wip:add_model')
        context['submit_label'] = 'Добавить'
        return context

    def form_valid(self, form):
        name = form.cleaned_data['name']
        status = UserModelStatus.objects.filter(user=self.request.user, is_initial=True).order_by('order').first()
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
        return redirect(reverse('wip:models', kwargs={'username': self.request.user.username}))


class WipModelUpdate(FormView):
    form_class = EditModelForm
    template_name = 'wip/model_edit.html'

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
        context['submit_url'] = reverse('wip:edit_model', kwargs={'model_id': self.kwargs['model_id']})
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
            'count': model.unit_count,
            'groups': model.groups.all()
        }
        return initial

    def form_valid(self, form):
        model = self.get_model()
        model.name = form.cleaned_data['name']
        if form.cleaned_data['groups']:
            model.groups.clear()
            for group in form.cleaned_data['groups']:
                model.groups.add(group)
        model.battlescribe_unit = form.cleaned_data['bs_unit']
        model.kill_team = form.cleaned_data['bs_kill_team']
        model.buy_date = form.cleaned_data['buy_date']
        if model.user_status != form.cleaned_data['status']:
            progress = ModelProgress(model=model,
                                     title="Смена статуса на: %s" % model.user_status.transition_title,
                                     time=0,
                                     user_status=model.user_status,
                                     datetime=datetime.datetime.now())
            progress.save()
        model.user_status = form.cleaned_data['status']
        model.hidden = form.cleaned_data['hidden']
        model.unit_count = form.cleaned_data['count']
        model.save()
        return redirect(reverse('wip:models', kwargs={'username': self.request.user.username}))


@login_required(login_url='/wip/accounts/login')
def delete_model(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model_progress = ModelProgress.objects.filter(model=model)
    model_progress.delete()
    model_images = ModelImage.objects.filter(model=model)
    model_images.delete()
    model.delete()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


class WipModelStatusActions(View):
    def get_model(self) -> Model:
        return Model.objects.get(id=self.kwargs['model_id'], user=self.request.user)

    def get(self, *args, **kwargs):
        self.get_model().change_status(self.kwargs['next_status'])
        return redirect(reverse('wip:models', kwargs={'username': self.request.user.username}))


class WipModelProgress(ListView):
    model = ModelProgress
    context_object_name = 'progress_items'
    template_name = 'wip/progress.html'

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
    template_name = 'wip/progress_form.html'
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
        context['submit_url'] = reverse('wip:add_progress', kwargs={
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
        return redirect(reverse('wip:progress', args=(model.user.username, model.id,)))


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
        context['submit_url'] = reverse('wip:edit_progress', kwargs={
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
        return redirect(reverse('wip:progress', args=(model.user.username, model.id,)))


@login_required(login_url='/wip/accounts/login')
def delete_progress(request, model_id, progress_id):
    model = Model.objects.get(id=model_id, user=request.user)
    progress = ModelProgress.objects.get(id=progress_id, model=model)
    images = ModelImage.objects.filter(progress=progress)
    images.delete()
    model = progress.model
    progress.delete()
    return redirect(reverse('wip:progress', args=(model.user.username, model.id,)))


class WipUserInventory(ListView):
    model = PaintInventory
    template_name = 'wip/inventory.html'
    context_object_name = 'items'

    def get_queryset(self):
        queryset = PaintInventory.objects.filter(user=self.request.user)\
            .order_by('paint__vendor__name', 'paint__type', 'paint__name')
        form = self.get_filter_form()
        if form.is_valid():
            if form.cleaned_data['vendor'] is not None:
                queryset = queryset.filter(paint__vendor=form.cleaned_data['vendor'])
            if form.cleaned_data['type'] != '':
                queryset = queryset.filter(paint__type=form.cleaned_data['type'])
            if form.cleaned_data['wish']:
                queryset = queryset.filter(wish=True)
            if form.cleaned_data['has']:
                queryset = queryset.filter(has=True)
        return queryset

    def get_filter_form(self):
        return InventoryFilterForm(self.request.GET)
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['filter_form'] = self.get_filter_form()
        return context


class WipUserInventoryManage(FormView):
    form_class = PaintInventoryManageForm
    template_name = 'wip/inventory_manage.html'

    def get_form(self, form_class=None):
        return self.form_class(self.request.user, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendors'] = PaintVendor.objects.all().values('id', 'name')
        paint_by_vendor = {}
        for vendor in context['vendors']:
            paint_by_vendor[vendor['name']] = []
            for paint in Paint.objects.filter(vendor_id=vendor['id']):
                paint_by_vendor[vendor['name']].append({'id': paint.id, 'name': str(paint)})
        context['paint_by_vendor'] = paint_by_vendor
        return context

    def form_valid(self, form):
        user_existed_inventory = PaintInventory.objects.filter(Q(user=self.request.user))
        inventory = self.prepare_inventory(user_existed_inventory.filter(Q(has=True)), form.cleaned_data['has'],
                                           has=True)
        inventory.extend(self.prepare_inventory(user_existed_inventory.filter(Q(wish=True)), form.cleaned_data['wish'],
                                                wish=True))
        PaintInventory.objects.bulk_create(inventory)
        return redirect(reverse('wip:inventory'))

    def prepare_inventory(self, existed_inventory, form_paints, has=False, wish=False):
        inventory = []
        existed_paints = list(map(lambda x: x.paint, existed_inventory.filter(Q(paint__in=form_paints))))
        to_delete = existed_inventory.filter(~Q(paint__in=form_paints))
        to_save = list(filter(lambda x: x not in existed_paints, form_paints))  # list(set(a) - set(b))
        to_delete.delete()
        for paint in to_save:
            inventory.append(PaintInventory(user=self.request.user, paint=paint, has=has, wish=wish))
        return inventory


@login_required(login_url='/wip/accounts/login')
def manage(request):
    return render(request, 'wip/manage/index.html')


class WipUserStatusGroupManage(ListView):
    model = StatusGroup
    template_name = 'wip/manage/status_group/index.html'
    context_object_name = 'items'

    def get_queryset(self):
        queryset = StatusGroup.objects.filter(user=self.request.user) \
            .order_by('order')
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['user'] = self.request.user
        return context


class WipUserStatusGroupManageCreate(FormView):
    form_class = StatusGroupForm
    template_name = 'wip/manage/status_group/add.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление группы статусов'
        context['submit_url'] = reverse('wip:manage_status_group_add')
        context['submit_label'] = 'Добавить'
        return context

    def form_valid(self, form):
        record = StatusGroup(name=form.cleaned_data['name'], user=self.request.user, order=form.cleaned_data['order'])
        record.save()
        return redirect(reverse('wip:manage_status_group_list'))


class WipUserStatusGroupManageUpdate(FormView):
    form_class = StatusGroupForm
    template_name = 'wip/manage/status_group/edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование группы статусов'
        context['submit_url'] = reverse('wip:manage_status_group_edit', kwargs={'status_group_id': self.kwargs['status_group_id']})
        context['submit_label'] = 'Сохранить'
        return context

    def get_record(self):
        return StatusGroup.objects.filter(user=self.request.user, id=self.kwargs['status_group_id']).first()

    def get_initial(self):
        record = self.get_record()
        initial = {
            'name': record.name,
            'order': record.order
        }
        return initial

    def form_valid(self, form):
        record = self.get_record()
        record.name = form.cleaned_data['name']
        record.order = form.cleaned_data['order']
        record.save()
        return redirect(reverse('wip:manage_status_group_list'))


@login_required(login_url='/wip/accounts/login')
def delete_user_status_group(request, status_group_id):
    record = StatusGroup.objects.get(id=status_group_id, user=request.user)
    record.delete()
    return redirect(reverse('wip:manage_status_group_list'))


class WipUserStatusManage(ListView):
    model = UserModelStatus
    template_name = 'wip/manage/status/index.html'
    context_object_name = 'items'

    def get_queryset(self):
        queryset = UserModelStatus.objects.filter(user=self.request.user) \
            .order_by('order')
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['user'] = self.request.user
        return context


class WipUserStatusManageCreate(FormView):
    form_class = UserStatusForm
    template_name = 'wip/manage/status/add.html'

    def get_form_kwargs(self):
        parent_kwargs = super().get_form_kwargs()
        parent_kwargs['user'] = self.request.user
        return parent_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление статуса'
        context['submit_url'] = reverse('wip:manage_status_add')
        context['submit_label'] = 'Добавить'
        return context

    def form_valid(self, form):
        record = UserModelStatus(
            name=form.cleaned_data['name'],
            slug=form.cleaned_data['slug'],
            transition_title=form.cleaned_data['transition_title'],
            user=self.request.user,
            order=form.cleaned_data['order'],
            previous=form.cleaned_data['previous'],
            next=form.cleaned_data['next'],
            group=form.cleaned_data['group'],
            is_initial=True if form.cleaned_data['is_initial'] else False,
            is_final=True if form.cleaned_data['is_final'] else False,
        )
        record.save()
        return redirect(reverse('wip:manage_status_list'))


class WipUserStatusManageUpdate(FormView):
    form_class = UserStatusForm
    template_name = 'wip/manage/status/edit.html'

    def get_form_kwargs(self):
        parent_kwargs = super().get_form_kwargs()
        parent_kwargs['user'] = self.request.user
        return parent_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование статуса'
        context['submit_url'] = reverse('wip:manage_status_edit', kwargs={'status_id': self.kwargs['status_id']})
        context['submit_label'] = 'Сохранить'
        return context

    def get_record(self) -> UserModelStatus:
        return UserModelStatus.objects.filter(user=self.request.user, id=self.kwargs['status_id']).first()

    def get_initial(self):
        record = self.get_record()
        initial = {
            'name': record.name,
            'slug': record.slug,
            'transition_title': record.transition_title,
            'user': record.user,
            'order': record.order,
            'previous': record.previous,
            'next': record.next,
            'group': record.group,
            'is_initial': record.is_initial,
            'is_final': record.is_final
        }
        return initial

    def form_valid(self, form):
        record = self.get_record()
        record.name = form.cleaned_data['name']
        record.slug = form.cleaned_data['slug']
        record.transition_title = form.cleaned_data['transition_title']
        record.order = form.cleaned_data['order']
        record.previous = form.cleaned_data['previous']
        record.next = form.cleaned_data['next']
        record.group = form.cleaned_data['group']
        record.is_initial = form.cleaned_data['is_initial']
        record.is_final = form.cleaned_data['is_final']
        record.save()
        return redirect(reverse('wip:manage_status_list'))


@login_required(login_url='/wip/accounts/login')
def delete_user_status(request, status_id):
    record = UserModelStatus.objects.get(id=status_id, user=request.user)
    record.delete()
    return redirect(reverse('wip:manage_status_list'))


class WipUserModelGroupManage(ListView):
    model = ModelGroup
    template_name = 'wip/manage/model_group/index.html'
    context_object_name = 'items'

    def get_queryset(self):
        return ModelGroup.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['user'] = self.request.user
        return context


class WipUserModelGroupManageCreate(FormView):
    form_class = ModelGroupForm
    template_name = 'wip/manage/model_group/add.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление группы моделей'
        context['submit_url'] = reverse('wip:manage_model_group_add')
        context['submit_label'] = 'Добавить'
        return context

    def form_valid(self, form):
        record = ModelGroup(name=form.cleaned_data['name'], user=self.request.user)
        record.save()
        return redirect(reverse('wip:manage_model_group_list'))


class WipUserModelGroupManageUpdate(FormView):
    form_class = ModelGroupForm
    template_name = 'wip/manage/model_group/edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование группы моделей'
        context['submit_url'] = reverse('wip:manage_model_group_edit',
                                        kwargs={'model_group_id': self.kwargs['model_group_id']})
        context['submit_label'] = 'Сохранить'
        return context

    def get_record(self):
        return ModelGroup.objects.filter(user=self.request.user, id=self.kwargs['model_group_id']).first()

    def get_initial(self):
        record = self.get_record()
        initial = {
            'name': record.name
        }
        return initial

    def form_valid(self, form):
        record = self.get_record()
        record.name = form.cleaned_data['name']
        record.save()
        return redirect(reverse('wip:manage_model_group_list'))


@login_required(login_url='/wip/accounts/login')
def delete_user_model_group(request, model_group_id):
    record = ModelGroup.objects.get(id=model_group_id, user=request.user)
    record.delete()
    return redirect(reverse('wip:manage_model_group_list'))


class ApiWipBasicAuthViewSet(viewsets.ModelViewSet):
    authentication_classes = [authentication.BasicAuthentication]


class ApiWipModelsViewSet(ApiWipBasicAuthViewSet):
    queryset = Model.objects.all()
    serializer_class = ModelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        old_date = timezone.now() - datetime.timedelta(days=2000)
        return super().get_queryset(*args, **kwargs).annotate(last_record=Max('progress__datetime', default=old_date))\
            .filter(user=self.request.user)\
            .order_by('-last_record', 'buy_date', 'created')


class ApiWipUserModelStatusesViewSet(ApiWipBasicAuthViewSet):
    queryset = UserModelStatus.objects.all()
    serializer_class = UserModelStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs)\
            .filter(user=self.request.user)\
            .order_by('order')