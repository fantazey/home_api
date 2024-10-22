from django import forms

from .models import UserModelStatus, StatusGroup


class UserSettingsForm(forms.Form):
    telegram_name = forms.CharField(label="Телеграм")


class UserStatusGroupForm(forms.ModelForm):
    class Meta:
        model = StatusGroup
        fields = ['name', 'order']


class UserModelStatusForm(forms.ModelForm):
    class Meta:
        model = UserModelStatus
        fields = ['name', 'transition_title', 'order', 'previous', 'next', 'group', 'is_initial', 'is_final']
