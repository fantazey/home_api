from datetime import datetime

from django import forms


class AddModelForm(forms.Form):
    name = forms.CharField(label='Название модели', max_length=500)
    in_inventory = forms.BooleanField(label='Куплено', required=False)


class AddProgressForm(forms.Form):
    title = forms.CharField(label='Название', max_length=500)
    description = forms.CharField(label='Подробнее', widget=forms.Textarea, required=False)
    date = forms.DateTimeField(label='Дата проведения работы', initial=datetime.now)


class LoginForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=40)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput, max_length=40)


class RegistrationForm(LoginForm):
    first_name = forms.CharField(label='Имя', max_length=40)
