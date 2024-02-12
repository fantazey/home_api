from django.forms import ModelForm,ImageField, CharField, IntegerField, ChoiceField, Form

from .models import Postcard


def build_country_choices():
    c = ['Россия', 'Германия', 'Нидерланды']
    return [(x,x) for x in c]


class PostcardForm(ModelForm):
    """

    """
    image = ImageField(label='фотка')
    sender = CharField(max_length="50", label="отправитель")
    country = ChoiceField(label='страна', choices=build_country_choices)
    travel_time = IntegerField(label="время в пути")

    class Meta:
        model = Postcard
        fields = ('image', 'sender', 'country', 'travel_time')

class LibraryAddForm(Form):
    """

    """
    image = ImageField(label='фотка')