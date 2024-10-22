from datetime import datetime, date

from django import forms
from django.core.exceptions import ValidationError

from work_in_progress.battlescribe.models import BSCategory, BSUnit, KillTeam
from work_in_progress.manage.models import UserModelStatus


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
                key = "pk"
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

    class BSKillTeamChoiceField(forms.ModelChoiceField):
        def label_from_instance(self, obj: KillTeam):
            return obj.name

    name = forms.CharField(label='Название модели', max_length=500)
    status = forms.ModelChoiceField(label='Статус', queryset=None, required=False)
    hidden = forms.BooleanField(label='Скрыть', required=False, initial=False)
    buy_date = forms.DateField(label='Дата покупки', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    bs_category = BSCategoryChoiceField(label="Категория из BattleScribe",
                                        queryset=BSCategory.objects.all(),
                                        widget=forms.Select(attrs={'class': 'ui fluid search selection dropdown'}),
                                        required=False)
    bs_unit = BSUnitChoiceField(label="Модель из BattleScribe",
                                queryset=BSUnit.objects.all(),
                                widget=forms.Select(attrs={'class': 'ui fluid search selection dropdown'}),
                                required=False)
    bs_kill_team = BSKillTeamChoiceField(label="КТ отряд из BattleScribe",
                                      queryset=KillTeam.objects.all(),
                                      widget=forms.Select(attrs={'class': 'ui fluid search selection dropdown'}),
                                      required=False)
    count = forms.IntegerField(label="Количество миниатюр", required=False, initial=1)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].queryset = UserModelStatus.objects.filter(user=user)


class EditModelForm(forms.Form):
    name = forms.CharField(label='Название модели', max_length=500)
    buy_date = forms.DateField(label='Дата покупки', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    bs_category = AddModelForm.BSCategoryChoiceField(label="Категория из BattleScribe",
                                                     queryset=BSCategory.objects.all(),
                                                     widget=forms.Select(
                                                         attrs={'class': 'ui fluid search selection dropdown'}
                                                     ),
                                                     required=False)
    bs_unit = AddModelForm.BSUnitChoiceField(label="Модель из BattleScribe",
                                             queryset=BSUnit.objects.all(),
                                             widget=forms.Select(attrs={'class': 'ui fluid search selection dropdown'}),
                                             required=False)
    bs_kill_team = AddModelForm.BSKillTeamChoiceField(label="КТ отряд из BattleScribe",
                                                   queryset=KillTeam.objects.all(),
                                                   widget=forms.Select(
                                                       attrs={'class': 'ui fluid search selection dropdown'}
                                                   ),
                                                   required=False)
    status = forms.ModelChoiceField(label="Статус", queryset=None)
    images = forms.ImageField(label="Картиночки",
                              widget=forms.ClearableFileInput(attrs={'multiple': True}),
                              required=False)
    hidden = forms.BooleanField(label="Скрыть", required=False, initial=False)
    count = forms.IntegerField(label="Количество миниатюр", required=False, initial=1)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].queryset = UserModelStatus.objects.filter(user=user)


class AddProgressForm(forms.Form):
    title = forms.CharField(label='Название', max_length=500)
    description = forms.CharField(label='Подробнее', widget=forms.Textarea, required=False)
    date = forms.DateTimeField(label='Дата проведения работы', initial=datetime.now)
    time = forms.FloatField(label="Затраченое время", initial=0.0)
    status = forms.ModelChoiceField(label="В статусе", queryset=None)
    images = forms.ImageField(label="Картиночки",
                              widget=forms.ClearableFileInput(attrs={'multiple': True}),
                              required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].queryset = UserModelStatus.objects.filter(user=user)


class ModelFilterForm(forms.Form):
    status = forms.ModelChoiceField(label="Статус", required=False, queryset=None, blank=True)
    page_size = forms.ChoiceField(label="На странице", choices=((x, x) for x in [12, 24, 900]), required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].queryset = UserModelStatus.objects.filter(user=user)


YEAR_CHOICES = ((x, x) for x in range(date.today().year, 2021, -1))


class WorkMapFilterForm(forms.Form):
    work_map_year = forms.ChoiceField(label="Год",
                                      choices=YEAR_CHOICES,
                                      required=False)

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data
        if 'work_map_year' in cleaned_data and len(cleaned_data['work_map_year']) > 0:
            cleaned_data['work_map_year'] = int(cleaned_data['work_map_year'])
        else:
            cleaned_data['work_map_year'] = self.initial['work_map_year']
        return cleaned_data
