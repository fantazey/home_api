from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from .models import Model


def index(request):
    if request.user.is_authenticated:
        results = Model.objects.all()
        context = {'models': results}
        return render(request, 'wip/index.html', context)
    else:
        return render(request, 'wip/login.html')


def log_in(request):
    if request.method == 'GET':
        return render(request, 'wip/login.html')

    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is None:
        return HttpResponseBadRequest("ошибка при входе")

    login(request, user)
    return redirect('/wip/')


def register(request):
    # if request.user.is_authenticated:
    #     return redirect('/wip')
    if request.method == 'GET':
        return render(request, 'wip/register.html')
    username = request.POST['username']
    password = request.POST['password']
    if User.objects.filter(username=username).exists():
        return HttpResponseBadRequest("такой пользователь существует")

    user = User(username=username)
    user.set_password(password)
    user.save()
    user = authenticate(request, username=username, password=password)
    if user is None:
        return HttpResponseBadRequest("ошибка при создании пользователя")

    login(request, user)
    return redirect('/wip/')


def log_out(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('/wip')