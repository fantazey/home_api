import datetime

from django.db import models


class Postcard(models.Model):
    image = models.ImageField(upload_to='postcard', verbose_name='лицевая сторона')
    sender = models.CharField(max_length=50, verbose_name='имя отправителя')
    country = models.CharField(max_length=50, verbose_name='страна отправления')
    travel_time = models.IntegerField(verbose_name='дней в пути')
    date_receiving = models.DateField(verbose_name='дата получения открытки', default=datetime.date.today())


    class Meta:
        verbose_name = 'Полученная открытка'
        verbose_name_plural = 'Полученные открытки'


class Library(models.Model):
    image = models.ImageField(upload_to='library', verbose_name='картинка')
    is_reserved = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Открытка для отправления'
        verbose_name_plural = 'Открытки для отправления'


class Address(models.Model):
    postcard = models.OneToOneField(Library, on_delete=models.RESTRICT)
    name = models.CharField(max_length=50, verbose_name='ФИО получателя')
    address = models.CharField(max_length=70, verbose_name='адрес получутеля')
    postcode = models.CharField(max_length=8, verbose_name='индекс')


