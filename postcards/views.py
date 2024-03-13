from django.shortcuts import render, redirect
from .models import Postcard, Library, Address
from django.views.generic.edit import CreateView
from .forms import PostcardForm, LibraryAddForm, AddressAddForm, LoginForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


def log_in(request):
    if request.user.is_authenticated:
        return redirect('postcards:index')

    if request.method == 'GET':
        form = LoginForm()
        return render(request, 'postcards/login.html', {'form': form})

    form = LoginForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('postcards:index')
    return render(request, 'postcards/login.html', {'form': form})


def log_out(request):
    logout(request)
    return redirect('postcards:index')


def index(request):
    return render(request,
                  'postcards/index.html',
                  {
                      'postcards': Postcard.objects.all().order_by('date_receiving'),
                      'user': request.user
                  })


class PostcardCreateView(CreateView):
    template_name = 'postcards/add.html'
    form_class = PostcardForm
    success_url = '/postcards'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@login_required(login_url='/postcards/login')
def edit(request, id):
    f = Postcard.objects.get(id=id)
    if request.method == 'GET':
        p = PostcardForm(initial={
            'sender': f.sender,
            'travel_time': f.travel_time,
            'country': f.country,
            'image': f.image
        })
        return render(request, 'postcards/edit.html', {'form': p, 'title': 'редактирование открытки', 'postcard': f})
    if request.method == 'POST':
        p = PostcardForm(request.POST, request.FILES)
        if p.is_valid():
            f.sender = p.cleaned_data['sender']
            f.travel_time = p.cleaned_data['travel_time']
            f.image = p.cleaned_data['image']
            f.country = p.cleaned_data['country']
            f.save()
            return redirect('postcards:index')
        return render(request, 'postcards/edit.html', {'form': p, 'title': 'редактирование открытки', 'postcard': f})


def delete(request, id):
    f = Postcard.objects.get(id=id)
    if request.method == 'GET':
        f.delete()
        return redirect('postcards:index')


def library(request):
    """
    главная страница со списком открыток которые я могу отправить
    """
    postcards = Library.objects.all()
    return render(request, 'postcards/library/library.html', {'postcards': postcards})


def library_delete(request, id):
    f = Library.objects.get(id=id)
    if request.method == 'GET':
        f.delete()
        return redirect('postcards:library')


def library_add(request):
    if request.method == 'GET':
        form = LibraryAddForm()
        return render(request, 'postcards/library/add.html', {'form': form})
    if request.method == 'POST':
        form = LibraryAddForm(request.POST, request.FILES)
        if form.is_valid():
            l = Library()
            l.image = form.cleaned_data['image']
            l.save()
            return redirect('postcards:library')
        return render(request, 'postcards/library/add.html', {'form': form})


def add_address(request, id):
    if request.method == 'GET':
        p = Library.objects.get(id=id)
        form = AddressAddForm()
        return render(request, 'postcards/address.html', {'form': form, 'postcard': p})
    if request.method == 'POST':
        form = AddressAddForm(request.POST)
        lp = Library.objects.get(id=id)
        if form.is_valid():
            address = Address()
            address.name = form.cleaned_data['name']
            address.address = form.cleaned_data['address']
            address.postcode = form.cleaned_data['postcode']
            address.postcard_id = lp.id
            address.save()

            lp.is_reserved = True
            lp.save()

            return redirect('postcards:library')
    return render(request, 'postcards/address.html', {'form': None, 'postcard': None})
