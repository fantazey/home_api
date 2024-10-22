from django import forms

from .models import Paint, PaintVendor, PaintInventory


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
