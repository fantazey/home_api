from math import trunc
from django import template
from django.forms import Form

register = template.Library()


@register.filter(name='duration')
def duration(record: float) -> str:
    if record is None:
        return ""
    hours = trunc(record)
    decimal_minutes = record - hours
    minutes = trunc(decimal_minutes * 60)
    return '%sч %sм' % (hours, minutes)


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    for k in [k for k, v in query.items() if not v]:
        del query[k]
    return query.urlencode()


@register.filter(name="get_field")
def get_field(form: Form, field_name: str):
    return form.fields[field_name].get_bound_field(form, field_name)
