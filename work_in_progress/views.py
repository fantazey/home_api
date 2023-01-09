import datetime

from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, Http404
from django.urls import reverse
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
    user_models = Model.objects.annotate(last_record=Max('modelprogress__datetime')).filter(user__username=username).order_by('-last_record', 'buy_date', 'created')
    if form.is_valid():
        user_models = user_models.filter(status=form.cleaned_data['status'])
    if request.user != user:
        user_models = user_models.filter(hidden=False)

    progress = ModelProgress.objects.filter(model__user=user)
    progress_by_date = {}
    for progress in progress:
        d = progress.datetime.date().strftime("%d-%m-%Y")
        progress_by_date[d] = True
    date_map = build_map(progress_by_date)
    return render(request, 'wip/models.html', {'models': user_models, 'user': user, 'filter_form': form, 'date_map': date_map})


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
        value = int(date_str in keys)
        week[wd] = (x, y, value,)
        if wd == 6:
            date_map.append(week)
            week_num += 1
            week = [None] * 7
        current_date = current_date + datetime.timedelta(days=1)
    return date_map


@login_required(login_url='/wip/accounts/login')
def add_model(request):
    if request.method == 'GET':
        form = AddModelForm()
        return render(request, 'wip/add_model.html', {'form': form})
    form = AddModelForm(request.POST)
    if form.is_valid():
        name = form.cleaned_data['name']
        model = Model(name=name, user=request.user)
        if form.cleaned_data['bs_unit']:
            model.battlescribe_unit = form.cleaned_data['bs_unit']
        status = Model.Status.WISHED
        progress_title = "Захотелось новую модельку"
        if form.cleaned_data['in_inventory']:
            status = Model.Status.IN_INVENTORY
            progress_title = "Куплено"
            if form.cleaned_data['buy_date']:
                model.buy_date = form.cleaned_data['buy_date']
        model.hidden = form.cleaned_data['hidden']
        model.status = status
        model.save()
        progress = ModelProgress(datetime=datetime.datetime.now(), title=progress_title, model=model)
        progress.save()
    return redirect(reverse('wip:models', kwargs={'username': request.user.username}))


@login_required(login_url='/wip/accounts/login')
def edit_model(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    if request.method == 'GET':
        initial = {
            'name': model.name,
            'buy_date': model.buy_date.strftime('%Y-%m-%d') if model.buy_date is not None else None,
            'bs_unit': model.battlescribe_unit,
            'bs_category': model.battlescribe_unit.bs_category if model.battlescribe_unit is not None else None,
            'hidden': model.hidden
        }
        form = EditModelForm(initial=initial)
        return render(request, 'wip/edit_model.html', {'form': form, 'model': model})
    form = EditModelForm(request.POST)
    if form.is_valid():
        model.name = form.cleaned_data['name']
        if form.cleaned_data['bs_unit']:
            model.battlescribe_unit = form.cleaned_data['bs_unit']
        if form.cleaned_data['buy_date']:
            model.buy_date = form.cleaned_data['buy_date']
        model.hidden = form.cleaned_data['hidden']
        model.save()
        return redirect(reverse('wip:models', kwargs={'username': request.user.username}))
    return render(request, 'wip/edit_model.html', {'form': form, 'model': model})


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
    if request.method == 'GET':
        form = AddProgressForm()
        return render(request, 'wip/add_progress.html', {
            'title': 'Добавление прогресса по модели %s' % model.name,
            'model': model,
            'form': form
        })
    form = AddProgressForm(request.POST, request.FILES)
    if form.is_valid():
        progress = ModelProgress(model=model,
                                 title=form.cleaned_data['title'],
                                 description=form.cleaned_data['description'],
                                 time=form.cleaned_data['time'],
                                 status=model.status,
                                 datetime=form.cleaned_data['date'])
        progress.save()
        for file in request.FILES.getlist('images'):
            image = ModelImage(progress=progress, model=progress.model, image=file)
            image.save()
        return redirect(reverse('wip:progress', args=(model.user.username, model.id,)))

    return render(request, 'wip/add_progress.html', {
        'title': 'Добавление прогресса по модели %s' % model.name,
        'model': model,
        'form': form
    })


@login_required(login_url='/wip/accounts/login')
def edit_progress(request, model_id, progress_id):
    model = Model.objects.get(id=model_id, user=request.user)
    progress = ModelProgress.objects.get(id=progress_id, model=model)
    if request.method == 'GET':
        initial = {
            'title': progress.title,
            'description': progress.description,
            'date': progress.datetime,
            'time': progress.time,
            'images': progress.modelimage_set.values('image')
        }
        form = AddProgressForm(initial=initial)
        return render(request, 'wip/edit_progress.html', {
            'title': 'Редактирование записи покраса',
            'model': progress.model,
            'progress': progress,
            'form': form
        })
    form = AddProgressForm(request.POST, request.FILES)
    if form.is_valid():
        progress.title = form.cleaned_data['title']
        progress.description = form.cleaned_data['description']
        progress.time = form.cleaned_data['time']
        progress.datetime = form.cleaned_data['date']
        progress.save()
        for file in request.FILES.getlist('images'):
            image = ModelImage(progress=progress, model=progress.model, image=file)
            image.save()
        return redirect(reverse('wip:progress', args=(model.user.username, model.id,)))


@login_required()
def delete_progress(request, model_id, progress_id):
    model = Model.objects.get(id=model_id, user=request.user)
    progress = ModelProgress.objects.get(id=progress_id, model=model)
    images = ModelImage.objects.filter(progress=progress)
    images.delete()
    model = progress.model
    progress.delete()
    return redirect(reverse('wip:progress', args=(model.user.username, model.id,)))
