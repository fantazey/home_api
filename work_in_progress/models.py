from django.db import models
from django.contrib.auth.models import User


class Model(models.Model):
    class Status(models.TextChoices):
        WISHED = 'wished', 'Лежит в магазине'
        IN_INVENTORY = 'in_inventory', 'Лежит в шкафу'
        ASSEMBLING = 'assembling', 'Собирается'
        PRIMING = 'priming', 'Грунтуется'
        BATTLE_READY_PAINTING = 'battle_ready_painting', 'Крашу в базу'
        PARADE_READY_PAINTING = 'parade_ready_painting', 'Хайлайтю'
        BASE_DECORATING = 'base_decorating', 'Оформляю поставку'
        VARNISHING = 'varnishing', 'Задуваю лаком'
        DONE = 'done', 'Закончено'

    name = models.CharField(verbose_name="Название модели", max_length=500)
    status = models.CharField(verbose_name="Статус", max_length=200, choices=Status.choices, default=Status.WISHED)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.RESTRICT)
    created = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True, null=False, blank=False)
    updated = models.DateTimeField(verbose_name="Дата обновления", auto_now=True, null=False, blank=False)

    def __str__(self):
        return "%s - %s" % (self.name, self.status)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.status)


class ModelProgress(models.Model):
    title = models.CharField(verbose_name="Описание выполненной работы", max_length=500)
    description = models.TextField(verbose_name="Подробности выполнененной работы")
    datetime = models.DateTimeField(verbose_name="Дата записи")
    model = models.ForeignKey(Model, on_delete=models.RESTRICT, verbose_name="Прогресс")

