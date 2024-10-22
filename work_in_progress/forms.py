from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['username'].max_length = 40
        self.fields['password'].label = 'Пароль'
        self.fields['password'].max_length = 40


class RegistrationForm(forms.Form):
    first_name = forms.CharField(label='Имя', max_length=40, required=True)
    telegram_name = forms.CharField(label='Телеграм', max_length=40, required=False)
    username = forms.CharField(label='Логин', max_length=40, required=True)
    password = forms.CharField(label='Пароль', max_length=40, required=True,
                               widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
