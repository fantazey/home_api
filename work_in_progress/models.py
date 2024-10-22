from django.contrib.auth.models import User
from django.db import models


"""
модуль кт:
1) список юнитов + оружие к ним + парсинг правил, у каждого юнита имя + профессия, в боте список оперативников из тимы, 
по выбору оперативника его характеристики, отдельная кнопка на аппендикс со спец правилами оружия
2) список уловок тактических - распарсить
3) список уловок стратегических - распарсить
4) шедулер на обновление данных батл скрайба из экселя и хранение этих данных в базе


модуль инвентаря:
1) краски - виш лист/инвентори: бренд, цвет, количество, ссылка, аналоги
2) инструменты виш лист/инвентори: бренд, название, ссылка
3) химия - виш лист/инвентори: бренд,  название, ссылка
"""


class Artist(models.Model):
    user = models.OneToOneField(User, verbose_name="Пользователь", on_delete=models.RESTRICT)
    telegram_name = models.CharField(verbose_name="Ник в телеге", max_length=200, unique=True)

    class Meta:
        verbose_name = "Красильщик"
        verbose_name_plural = "Красильщики"

    def __str__(self):
        return self.user.username
