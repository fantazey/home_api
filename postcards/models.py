import datetime

from django.db import models


class Postcard(models.Model):
    '''
    определили модель карточки открытки. Содержит в себе фотографию открытки, имя и страну отправителя, время в пути
    '''

    image = models.ImageField(upload_to='postcard', verbose_name='лицевая сторона')
    sender = models.CharField(max_length=50, verbose_name='имя отправителя')
    country = models.CharField(max_length=50, verbose_name='страна отправления')
    travel_time = models.IntegerField(verbose_name='дней в пути')
    date_receiving = models.DateField(verbose_name='дата получения открытки', default=datetime.date.today())


    class Meta:
        verbose_name = 'Полученная открытка'
        verbose_name_plural = 'Полученные открытки'

    '''определили модели карточки открытки из бибилиотеки открыток к отправке'''


class Library(models.Model):
    image = models.ImageField(upload_to='library', verbose_name='картинка')

    class Meta:
        verbose_name = 'Открытка для отправления'
        verbose_name_plural = 'Открытки для отправления'
