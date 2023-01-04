import datetime

from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from .models import Model, ModelProgress
from .forms import AddModelForm, LoginForm, AddProgressForm, RegistrationForm


def log_in(request):
    if request.method == 'GET':
        form = LoginForm()
        return render(request, 'wip/login.html', {'form': form})
    form = LoginForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is None:
            return HttpResponseBadRequest("ошибка при входе")
        login(request, user)
        return redirect(reverse('wip:index'))
    return render(request, 'wip/login.html', {'form': form})


def register(request):
    if request.user.is_authenticated:
        return redirect(reverse('wip:index'))
    if request.method == 'GET':
        form = RegistrationForm()
        return render(request, 'wip/register.html', {'form': form})
    form = RegistrationForm(request.POST)
    if not form.is_valid():
        return render(request, 'wip/register.html', {'form': form})
    username = form.cleaned_data['username']
    password = form.cleaned_data['password']
    if User.objects.filter(username=username).exists():
        form.add_error('username', 'Пользователь существует')
        return render(request, 'wip/register.html', {'form': form})
    user = User(username=username)
    user.set_password(password)
    user.save()
    user = authenticate(request, username=username, password=password)
    if user is None:
        return HttpResponseBadRequest("ошибка при создании пользователя")

    login(request, user)
    return redirect(reverse('wip:index'))


def log_out(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse('wip:login'))


def index(request):
    if request.user.is_authenticated:
        models = Model.objects.filter(user=request.user)
        return render(request, 'wip/index.html', {'models': models})
    else:
        return redirect(reverse('wip:login'))


def add_model(request):
    if request.method == 'GET':
        form = AddModelForm()
        return render(request, 'wip/add_model.html', {'form': form})
    form = AddModelForm(request.POST)
    if form.is_valid():
        name = form.cleaned_data['name']
        model = Model(name=name, user=request.user)
        status = Model.Status.WISHED
        progress_title = "Захотелось новую модельку"
        if form.cleaned_data['in_inventory']:
            status = Model.Status.IN_INVENTORY
            progress_title = "Купил новую модельку"
        model.status = status
        model.save()
        progress = ModelProgress(datetime=datetime.datetime.now(), title=progress_title, model=model)
        progress.save()
    return redirect(reverse('wip:index'))


def put_in_inventory(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.put_in_inventory()
    return redirect(reverse('wip:index'))


def start_assembly(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_assembly()
    return redirect(reverse('wip:index'))


def finish_assembly(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_assembly()
    return redirect(reverse('wip:index'))


def start_priming(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_priming()
    return redirect(reverse('wip:index'))


def finish_priming(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_priming()
    return redirect(reverse('wip:index'))


def start_painting(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_painting()
    return redirect(reverse('wip:index'))


def finish_painting(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_painting()
    return redirect(reverse('wip:index'))


def start_parade_ready_painting(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_parade_ready_painting()
    return redirect(reverse('wip:index'))


def finish_parade_ready_painting(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_parade_ready_painting()
    return redirect(reverse('wip:index'))


def start_base_decoration(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_base_decoration()
    return redirect(reverse('wip:index'))


def finish_base_decoration(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_base_decoration()
    return redirect(reverse('wip:index'))


def start_varnishing(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.start_varnishing()
    return redirect(reverse('wip:index'))


def finish_varnishing(request, model_id):
    model = Model.objects.get(id=model_id, user=request.user)
    model.finish_varnishing()
    return redirect(reverse('wip:index'))


def view_progress(request, model_id):
    model = Model.objects.get(id=model_id)
    progress_items = ModelProgress.objects.filter(model=model)
    return render(request, 'wip/view_progress.html', {
        'model': model,
        'progress_items': progress_items
    })


def track_progress(request, model_id):
    model = Model.objects.get(id=model_id)
    if request.method == 'GET':
        form = AddProgressForm()
        return render(request, 'wip/track_progress.html', {
            'model': model,
            'form': form
        })
    form = AddProgressForm(request.POST)
    if form.is_valid():
        progress = ModelProgress(model=model,
                                 title=form.cleaned_data['title'],
                                 description=form.cleaned_data['description'],
                                 datetime=form.cleaned_data['date'])
        progress.save()
        return redirect(reverse('wip:progress', args=(model.id,)))

    return render(request, 'wip/track_progress.html', {
        'model': model,
        'form': form
    })