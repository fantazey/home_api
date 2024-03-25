from django.shortcuts import render, redirect, reverse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import ListView, View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import Postcard, Library, Address
from .forms import PostcardForm, LibraryAddForm, AddressAddForm, LoginForm


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


class PostcardsListView(ListView):
    model = Postcard
    context_object_name = 'postcards'
    paginate_by = 5
    ordering = ['id']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class PostcardCreateView(CreateView):
    template_name = 'postcards/add.html'
    form_class = PostcardForm
    success_url = '/postcards'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PostcardEditView(UpdateView):
    model = Postcard
    form_class = PostcardForm
    success_url = '/postcards'
    pk_url_kwarg = 'id'
    template_name_suffix = '_edit_form'

    def get_context_data(self, *args,  **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PostcardDeleteView(View):
    def get(self, *args, **kwargs):
        f = Postcard.objects.get(id=self.kwargs['id'])
        if self.request.method == 'GET':
            f.delete()
            return redirect('postcards:index')


def delete(request, id):
    f = Postcard.objects.get(id=id)
    if request.method == 'GET':
        f.delete()
        return redirect('postcards:index')


class LibraryListView(ListView):
    model = Library
    context_object_name = 'postcards'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


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
