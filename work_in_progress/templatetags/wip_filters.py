from math import trunc
from django import template

register = template.Library()


@register.filter(name='duration')
def duration(record: float) -> str:
    if record is None:
        return ""
    hours = trunc(record)
    decimal_minutes = record - hours
    minutes = trunc(decimal_minutes * 60)
    return '%sч %sм' % (hours, minutes)
