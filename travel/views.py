from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets

from .models import Place


def index(request):
    return render(request, 'travel/index.html')


class UserField(serializers.RelatedField):
    def to_representation(self, value: User):
        return f"{value.first_name} {value.last_name}"


class PlaceSerializer(serializers.ModelSerializer):
    user = UserField(many=False, read_only=True)

    class Meta:
        model = Place
        fields = '__all__'


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
