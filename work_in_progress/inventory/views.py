from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import FormView

from .forms import PaintInventoryManageForm, InventoryFilterForm
from .models import PaintInventory, Paint, PaintVendor


class WipUserInventory(ListView):
    model = PaintInventory
    template_name = 'wip/inventory/index.html'
    context_object_name = 'items'

    def get_queryset(self):
        queryset = PaintInventory.objects.filter(user=self.request.user) \
            .order_by('paint__vendor__name', 'paint__type', 'paint__name')
        form = self.get_filter_form()
        if form.is_valid():
            if form.cleaned_data['vendor'] is not None:
                queryset = queryset.filter(paint__vendor=form.cleaned_data['vendor'])
            if form.cleaned_data['type'] != '':
                queryset = queryset.filter(paint__type=form.cleaned_data['type'])
            if form.cleaned_data['wish']:
                queryset = queryset.filter(wish=True)
            if form.cleaned_data['has']:
                queryset = queryset.filter(has=True)
        return queryset

    def get_filter_form(self):
        return InventoryFilterForm(self.request.GET)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['filter_form'] = self.get_filter_form()
        return context


class WipUserInventoryManage(FormView):
    form_class = PaintInventoryManageForm
    template_name = 'wip/inventory/manage.html'

    def get_form(self, form_class=None):
        return self.form_class(self.request.user, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendors'] = PaintVendor.objects.all().values('id', 'name')
        paint_by_vendor = {}
        for vendor in context['vendors']:
            paint_by_vendor[vendor['name']] = []
            for paint in Paint.objects.filter(vendor_id=vendor['id']):
                paint_by_vendor[vendor['name']].append({'id': paint.id, 'name': str(paint)})
        context['paint_by_vendor'] = paint_by_vendor
        return context

    def form_valid(self, form):
        user_existed_inventory = PaintInventory.objects.filter(Q(user=self.request.user))
        inventory = self.prepare_inventory(user_existed_inventory.filter(Q(has=True)), form.cleaned_data['has'],
                                           has=True)
        inventory.extend(self.prepare_inventory(user_existed_inventory.filter(Q(wish=True)), form.cleaned_data['wish'],
                                                wish=True))
        PaintInventory.objects.bulk_create(inventory)
        return redirect(reverse('wip:inventory:inventory'))

    def prepare_inventory(self, existed_inventory, form_paints, has=False, wish=False):
        inventory = []
        existed_paints = list(map(lambda x: x.paint, existed_inventory.filter(Q(paint__in=form_paints))))
        to_delete = existed_inventory.filter(~Q(paint__in=form_paints))
        to_save = list(filter(lambda x: x not in existed_paints, form_paints))  # list(set(a) - set(b))
        to_delete.delete()
        for paint in to_save:
            inventory.append(PaintInventory(user=self.request.user, paint=paint, has=has, wish=wish))
        return inventory
