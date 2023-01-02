from django import forms


class AddModelForm(forms.Form):
    name = forms.CharField(label='Название модели')
    in_inventory = forms.BooleanField(label='Куплено', required=False)


class LoginForm(forms.Form):
    username = forms.CharField(label='Логин')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)