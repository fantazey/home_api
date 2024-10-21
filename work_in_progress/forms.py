from datetime import datetime, date

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm

from .models import BSCategory, BSUnit, Paint, PaintVendor, PaintInventory, KillTeam, UserModelStatus


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


class PaintInventoryManageForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vendors = PaintVendor.objects.all()
        self.vendors = []
        for vendor in vendors:
            paints = Paint.objects.filter(vendor=vendor)
            vendor_paints = ((x.id, str(x)) for x in paints)
            field = forms.MultipleChoiceField(
                label="Список красок",
                choices=vendor_paints,
                required=False,
                widget=forms.SelectMultiple(attrs={'size': '25'}))
            self.fields['paints_' + str(vendor.id)] = field
            paints_inventory = PaintInventory.objects.filter(user=user, paint__in=paints)

            if 'data' in kwargs:
                paints_inventory_has = ((x.id, str(x)) for x in paints)
            else:
                paints_inventory_has = ((x.paint.id, str(x.paint)) for x in paints_inventory.filter(has=True))

            field = forms.MultipleChoiceField(
                label="В наличии",
                choices=paints_inventory_has,
                required=False,
                widget=forms.SelectMultiple(attrs={'size': '25'}))
            self.fields['paints_has_from_vendor_' + str(vendor.id)] = field

            if 'data' in kwargs:
                paints_inventory_wish = ((x.id, str(x)) for x in paints)
            else:
                paints_inventory_wish = ((x.paint.id, str(x.paint)) for x in paints_inventory.filter(wish=True))

            field = forms.MultipleChoiceField(
                label="Надо купить",
                choices=paints_inventory_wish,
                required=False,
                widget=forms.SelectMultiple(attrs={'size': '25'}))
            self.fields['paints_wish_from_vendor_' + str(vendor.id)] = field
            self.vendors.append((vendor.id,
                                 vendor.name,
                                 'paints_' + str(vendor.id),
                                 'paints_has_from_vendor_' + str(vendor.id),
                                 'paints_wish_from_vendor_' + str(vendor.id)))

    def clean(self):
        cleaned_data = super().clean()
        paints_has = []
        paints_wish = []
        for v in self.vendors:
            vendor = PaintVendor.objects.get(id=v[0])
            if v[3] in cleaned_data:
                ids = list(map(lambda x: int(x), set(cleaned_data[v[3]])))
                selected_has_paints = Paint.objects.filter(vendor=vendor,
                                                           id__in=ids)
                paints_has.extend(selected_has_paints)
            if v[4] in cleaned_data:
                ids = list(map(lambda x: int(x), set(cleaned_data[v[4]])))
                selected_wish_paints = Paint.objects.filter(vendor=vendor,
                                                            id__in=ids)
                paints_wish.extend(selected_wish_paints)
        return {
            'has': paints_has,
            'wish': paints_wish
        }


class InventoryFilterForm(forms.Form):
    vendor = forms.ModelChoiceField(label="Производитель", queryset=PaintVendor.objects.all(), required=False)
    type = forms.ChoiceField(label="Тип", choices=(), required=False)
    status = forms.ChoiceField(label="Состояние",
                               choices=(('', '----'), ('wish', 'Надо купить'), ('has', 'В наличии')),
                               required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].choices = (('', '----'), *set((x, x) for x in Paint.objects.all().values_list('type',
                                                                                                          flat=True)))

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['wish'] = False
        cleaned_data['has'] = False
        if 'status' in cleaned_data:
            if cleaned_data['status'] == 'wish':
                cleaned_data['wish'] = True
            if cleaned_data['status'] == 'has':
                cleaned_data['has'] = True
        return cleaned_data
