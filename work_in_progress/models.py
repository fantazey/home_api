from django.db import models
from django.contrib.auth.models import User


class Model(models.Model):
    class ModelStatus(models.TextChoices):
        WISHED = 'washed', 'Лежит в магазине'
        IN_INVENTORY = 'in_inventory', 'Куплено'
        ASSEMBLING = 'assembling', 'Собирается'
        PRIMING = 'priming', 'Грунтуется'
        BATTLE_READY_PAINTING = 'battle_ready_painting', 'Крашу в базу'
        PARADE_READY_PAINTING = 'parade_ready_painting', 'Хайлайтю'
        BASE_DECORATING = 'base_decorating', 'Оформляю поставку'
        VARNISHING = 'varnishing', 'Задуваю лаком'
        DONE = 'done', 'Закончено'

    name = models.CharField(name="Название модели", max_length=500)
    status = models.CharField(name="Статус", max_length=200, choices=ModelStatus.choices, default=ModelStatus.WISHED)
    user = models.ForeignKey(User, related_name="Пользователь", on_delete=models.RESTRICT)

    def __str__(self):
        return "%s - %s" % (self.name, self.status)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.status)


class ModelProgress(models.Model):
    title = models.CharField(name="Описание выполненной работы", max_length=500)
    description = models.TextField(name="Подробности выполнененной работы")
    datetime = models.DateTimeField(name="Дата записи")
    model = models.ForeignKey(Model, on_delete=models.RESTRICT, related_name="Прогресс")

