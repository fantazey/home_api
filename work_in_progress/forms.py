from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError

from .models import BSCategory, BSUnit


class AddModelForm(forms.Form):

    class BSCategoryChoiceField(forms.ModelChoiceField):
        def label_from_instance(self, obj: BSCategory):
            return obj.name

    class BSUnitChoiceField(forms.ModelChoiceField):
        def label_from_instance(self, obj: BSUnit):
            return obj.name

        def prepare_value(self, value: BSUnit):
            if value:
                return '%s_%s' % (value.bs_category.pk, value.pk)
            return super().prepare_value(value)

        def to_python(self, value: str):
            if value in self.empty_values:
                return None
            value = value.split('_')[1]
            try:
                key = self.to_field_name or "pk"
                if isinstance(value, self.queryset.model):
                    value = getattr(value, key)
                value = self.queryset.get(**{key: value})
            except (ValueError, TypeError, self.queryset.model.DoesNotExist):
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": value},
                )
            return value


    name = forms.CharField(label='Название модели', max_length=500)
    in_inventory = forms.BooleanField(label='Куплено', required=False)
    bs_category = BSCategoryChoiceField(label="Категория из BattleScribe",
                                        queryset=BSCategory.objects.all(),
                                        widget=forms.Select(attrs={'class': 'ui fluid search selection dropdown'}),
                                        required=False)
    bs_unit = BSUnitChoiceField(label="Модель из BattleScribe",
                                queryset=BSUnit.objects.all(),
                                widget=forms.Select(attrs={'class': 'ui fluid search selection dropdown'}),
                                required=False)


class AddProgressForm(forms.Form):
    title = forms.CharField(label='Название', max_length=500)
    description = forms.CharField(label='Подробнее', widget=forms.Textarea, required=False)
    date = forms.DateTimeField(label='Дата проведения работы', initial=datetime.now)
    time = forms.FloatField(label="Затраченое время", initial=0.0)


class LoginForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=40)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput, max_length=40)


class RegistrationForm(LoginForm):
    first_name = forms.CharField(label='Имя', max_length=40)
