from django.forms import ModelForm, ImageField, CharField, IntegerField, ChoiceField, Form, DateField

from .models import Postcard


def build_country_choices():
    c = ['Россия', 'Германия', 'Нидерланды']
    return [(x, x) for x in c]


class PostcardForm(ModelForm):
    image = ImageField(label='фотка')
    sender = CharField(max_length="50", label="отправитель")
    country = ChoiceField(label='страна', choices=build_country_choices)
    travel_time = IntegerField(label="время в пути")
    date_receiving = DateField(label='дата получения')

    class Meta:
        model = Postcard
        fields = ('image', 'sender', 'country', 'travel_time', 'date_receiving')


class LibraryAddForm(Form):
    image = ImageField(label='фотка')


class AddressAddForm(Form):
    name = CharField(max_length="70", label='имя получателя')
    postcode = CharField(max_length="30", label='postcode')
    address = CharField(max_length="70", label='адрес')
