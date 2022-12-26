from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User


def index(request):
    if request.user.is_authenticated:
        return render(request, 'wip/index.html', {})
    else:
        return render(request, 'wip/login.html', {})


def log_in(request):
    if request.method == 'GET':
        return render(request, 'wip/login.html', {})

    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('/wip/')


def register(request):
    if request.method == 'GET':
        return render(request, 'wip/register.html', {})
    username = request.POST['username']
    password = request.POST['password']
    user = User(username=username)
    user.save()
    user.set_password(password)
    user.save()
    a_user = authenticate(request, username=username, password=password)
    if a_user is not None:
        login(request, user)
        return redirect('/wip/')
    return HttpResponseBadRequest("oh no")
