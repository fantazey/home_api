from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt
from json import dumps, loads
from .models import Measure


def index(request):
    return render(request, 'weather/index.html', {})


def get_last_100_measures(request):
    res = Measure.objects.order_by('date')[:100].values("id", "date", "temperature", "humidity")
    return HttpResponse(dumps(list(res), cls=DjangoJSONEncoder))


@csrf_exempt
def add_measure(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("")
    data = loads(request.body)
    m1 = Measure(date=data['date'], temperature=data['temperature'], humidity=data['humidity'])
    m1.save()
    data = Measure.objects.filter(id=m1.id).values("id", "date", "temperature", "humidity")
    data = dumps(list(data), cls=DjangoJSONEncoder)
    struct = loads(data)
    data = dumps(struct[0])
    return HttpResponse(data, content_type='application/json')
