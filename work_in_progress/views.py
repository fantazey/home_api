import datetime

from django.shortcuts import render, redirect
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max, Sum

from .models import Model, ModelProgress, ModelImage
from .forms import AddModelForm, LoginForm, AddProgressForm, RegistrationForm, EditModelForm, ModelFilterForm


def log_in(request):
    if request.user.is_authenticated:
        return redirect(reverse('wip:models', kwargs={'username': request.user.username}))

    if request.method == 'GET':
        form = LoginForm()
        return render(request, 'wip/login.html', {'form': form})

    form = LoginForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse('wip:models', kwargs={'username': request.user.username}))
        form.add_error("password", "Не правильный логин или пароль")
    return render(request, 'wip/login.html', {'form': form}, status=400)


def register(request):
    if request.user.is_authenticated:
        return redirect(reverse('wip:index'))

    if request.method == 'GET':
        form = RegistrationForm()
        return render(request, 'wip/register.html', {'form': form})

    form = RegistrationForm(request.POST)
    if not form.is_valid():
        return render(request, 'wip/register.html', {'form': form}, status=400)

    username = form.cleaned_data['username']
    password = form.cleaned_data['password']
    if User.objects.filter(username=username).exists():
        form.add_error('username', 'Пользователь существует')
        return render(request, 'wip/register.html', {'form': form}, status=400)

    user = User(username=username)
    user.set_password(password)
    user.save()
    user = authenticate(request, username=username, password=password)
    if user is None:
        form.add_error('username', 'ошибка при создании пользователя')
        return render(request, 'wip/register.html', {'form': form}, status=400)

    login(request, user)
    return redirect(reverse('wip:index'))


@login_required(login_url='/wip/accounts/login')
def log_out(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse('wip:login'))


def about(request):
    return render(request, 'wip/about.html')


def index(request):
    all_models = Model.objects.annotate(last_record=Max('modelprogress__datetime')).\
                filter(hidden=False).\
                order_by('-last_record')[:20]
    return render(request, 'wip/index.html', {'models': all_models})


def models(request, username):
    users = User.objects.filter(username=username)
    if not users.exists():
        return Http404("Пользователь не найден")
    user = users.first()
    form = ModelFilterForm(request.GET)
    user_models = Model.objects.annotate(last_record=Max('modelprogress__datetime'))\
        .filter(user__username=username)\
        .order_by('-last_record', 'buy_date', 'created')
    if form.is_valid():
        user_models = user_models.filter(status=form.cleaned_data['status'])
    if request.user != user:
        user_models = user_models.filter(hidden=False)

    progress_list = ModelProgress.objects.filter(model__user=user, time__gt=0)
    progress_by_date = {}
    for progress in progress_list:
        d = timezone.localtime(progress.datetime).date().strftime("%d-%m-%Y")
        if d not in progress_by_date.keys():
            progress_by_date[d] = 0
        progress_by_date[d] += progress.time
    date_map = build_map(progress_by_date)
    sum_time_by_status = progress_list.filter(status__isnull=False).values("status").annotate(total_time=Sum('time'))
    status_map = [(Model.Status(x['status']).label, x['total_time']) for x in sum_time_by_status]
    return render(request, 'wip/models.html', {
        'models': user_models,
        'user': user,
        'filter_form': form,
        'date_map': date_map,
        'time_status_map': status_map
    })


def build_map(progress_by_date):
    start = datetime.date(2023, 1, 1)
    end = datetime.date(2023, 12, 31)
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
        week[wd] = (x, y, value, current_date.day, x+5, y+8)
        if wd == 6:
            date_map.append(week)
            week_num += 1
            week = [None] * 7
        current_date = current_date + datetime.timedelta(days=1)
    return date_map


@login_required(login_url='/wip/accounts/login')
def add_model(request):
    context = {
        'title': 'Добавление модели в PileOfShame',
        'submit_url': reverse('wip:add_model'),
        'submit_label': 'Добавить'
    }
    if request.method == 'GET':
        context['form'] = AddModelForm()
        return render(request, 'wip/add_model.html', context)

    form = AddModelForm(request.POST)
    if not form.is_valid():
        context['form'] = form
        return render(request, 'wip/add_model.html', context)

    name = form.cleaned_data['name']
    model = Model(name=name,
                  user=request.user,
                  status=Model.Status.WISHED,
                  battlescribe_unit=form.cleaned_data['bs_unit'],
                  buy_date=form.cleaned_data['buy_date'],
                  hidden = form.cleaned_data['hidden'])

    progress_title = "Захотелось новую модельку"
    if form.cleaned_data['in_inventory']:
        model.status = Model.Status.IN_INVENTORY
        progress_title = "Куплено"

    model.save()
    progress = ModelProgress(datetime=datetime.datetime.now(), title=progress_title, model=model)
    progress.save()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def edit_model(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    context = {
        'title': 'Редактирование модели %s' % model,
        'submit_url': reverse('wip:edit_model', kwargs={'model_id': model_id}),
        'submit_label': 'Сохранить'
    }
    if request.method == 'GET':
        initial = {
            'name': model.name,
            'buy_date': model.buy_date.strftime('%Y-%m-%d') if model.buy_date is not None else None,
            'bs_unit': model.battlescribe_unit,
            'status': model.status,
            'bs_category': model.battlescribe_unit.bs_category if model.battlescribe_unit is not None else None,
            'hidden': model.hidden
        }
        context['form'] = EditModelForm(initial=initial)
        return render(request, 'wip/edit_model.html', context)
    form = EditModelForm(request.POST)
    if not form.is_valid():
        context['form'] = form
        return render(request, 'wip/edit_model.html', context)

    model.name = form.cleaned_data['name']
    model.battlescribe_unit = form.cleaned_data['bs_unit']
    model.buy_date = form.cleaned_data['buy_date']
    if model.status != form.cleaned_data['status']:
        progress = ModelProgress(model=model,
                                 title="Смена статуса на: %s" % Model.Status(form.cleaned_data['status']).label,
                                 time=0,
                                 status=model.status,
                                 datetime=datetime.datetime.now())
        progress.save()
    model.status = form.cleaned_data['status']
    model.hidden = form.cleaned_data['hidden']
    model.save()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def delete_model(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model_progress = ModelProgress.objects.filter(model=model)
    model_progress.delete()
    model.delete()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def put_in_inventory(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.put_in_inventory()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def start_assembly(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_assembly()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def finish_assembly(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_assembly()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def start_priming(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_priming()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def finish_priming(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_priming()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def start_painting(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_painting()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def finish_painting(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_painting()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def start_parade_ready_painting(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_parade_ready_painting()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def finish_parade_ready_painting(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_parade_ready_painting()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def start_base_decoration(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_base_decoration()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def finish_base_decoration(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_base_decoration()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def start_varnishing(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_varnishing()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def finish_varnishing(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_varnishing()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


def view_progress(request, username, model_id):
    users = User.objects.filter(username=username)
    if not users.exists():
        return Http404("Пользователь не найден")
    user = users.first()
    model = Model.objects.get(id=model_id, user=user)
    progress_items = ModelProgress.objects.filter(model=model).order_by('-datetime')
    total = progress_items.aggregate(Sum('time'))
    return render(request, 'wip/progress.html', {
        'model': model,
        'user': user,
        'total': total['time__sum'],
        'progress_items': progress_items
    })


@login_required(login_url='/wip/accounts/login')
def add_progress(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    context = {
        'title': 'Добавление прогресса для модели %s' % model,
        'model': model,
        'submit_url': reverse('wip:add_progress', kwargs={'model_id': model.id}),
        'button_label': 'Добавить'
    }
    if request.method == 'GET':
        initial = {
            'status': model.status,
        }
        context['form'] = AddProgressForm(initial=initial)
        return render(request, 'wip/edit_progress.html', context)

    form = AddProgressForm(request.POST, request.FILES)
    if form.is_valid():
        progress = ModelProgress(model=model,
                                 title=form.cleaned_data['title'],
                                 description=form.cleaned_data['description'],
                                 time=form.cleaned_data['time'],
                                 status=form.cleaned_data['status'],
                                 datetime=form.cleaned_data['date'])
        progress.save()
        progress.add_images(request.FILES.getlist('images'))
        return redirect(reverse('wip:progress', args=(model.user.username, model.id,)))

    context['form'] = form
    return render(request, 'wip/edit_progress.html', context)


@login_required(login_url='/wip/accounts/login')
def edit_progress(request, model_id, progress_id):
    model = Model.objects.get(id=model_id, user=request.user)
    progress = ModelProgress.objects.get(id=progress_id, model=model)
    context = {
        'title': 'Редактирование записи покраса %s для модели %s' % (progress, model),
        'model': model,
        'submit_url': reverse('wip:edit_progress', kwargs={'model_id': model.id, 'progress_id': progress.id}),
        'button_label': 'Сохранить'
    }
    if request.method == 'GET':
        initial = {
            'title': progress.title,
            'description': progress.description,
            'date': progress.datetime,
            'time': progress.time,
            'status': progress.status,
            'images': progress.modelimage_set.values('image')
        }
        context['form'] = AddProgressForm(initial=initial)
        return render(request, 'wip/edit_progress.html', context)
    form = AddProgressForm(request.POST, request.FILES)
    if form.is_valid():
        progress.title = form.cleaned_data['title']
        progress.description = form.cleaned_data['description']
        progress.time = form.cleaned_data['time']
        progress.datetime = form.cleaned_data['date']
        progress.status = form.cleaned_data['status']
        progress.save()
        progress.add_images(request.FILES.getlist('images'))
        return redirect(reverse('wip:progress', args=(model.user.username, model.id,)))
    context['form'] = form
    return render(request, 'wip/edit_progress.html', context)


@login_required()
def delete_progress(request, model_id, progress_id):
    model = Model.objects.get(id=model_id, user=request.user)
    progress = ModelProgress.objects.get(id=progress_id, model=model)
    images = ModelImage.objects.filter(progress=progress)
    images.delete()
    model = progress.model
    progress.delete()
    return redirect(reverse('wip:progress', args=(model.user.username, model.id,)))
