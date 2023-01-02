from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from .models import Model, ModelProgress
from .forms import AddModelForm, LoginForm


def index(request):
    if request.user.is_authenticated:
        results = Model.objects.all()
        context = {'models': results}
        return render(request, 'wip/index.html', context)
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
        if form.cleaned_data['in_inventory']:
            status = Model.Status.IN_INVENTORY
        model.status = status
        model.save()
    return redirect(reverse('wip:index'))


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
        form = LoginForm()
        return render(request, 'wip/register.html', {'form': form})
    form = LoginForm(request.POST)
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


def view_progress(request, model_id):
    model = Model.objects.get(id=model_id)
    progress_items = ModelProgress.objects.filter(model=model)
    return render(request, 'wip/view_progress.html', {
        'model': model,
        'progress_items': progress_items
    })
