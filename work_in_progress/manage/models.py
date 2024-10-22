from django.contrib.auth.models import User
from django.db import models


class UserModelStatus(models.Model):
    name = models.CharField(verbose_name="Название", max_length=500)
    slug = models.CharField(verbose_name="Слаг", max_length=500)
    transition_title = models.CharField(verbose_name="Заголовок в прогрессе модели при переходе в статус",
                                        max_length=500, null=True, blank=True)
    order = models.IntegerField(verbose_name="Порядковый номер", default=0)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.RESTRICT)
    previous = models.ForeignKey('self', verbose_name="Предыдущий статус", null=True, on_delete=models.RESTRICT,
                                 related_name="next_status")
    next = models.ForeignKey('self', verbose_name="Следующий статус", null=True, on_delete=models.RESTRICT,
                             related_name="previous_status")

    group = models.ForeignKey('StatusGroup', verbose_name="Группа", on_delete=models.RESTRICT, related_name="statuses",
                              null=True)
    is_initial = models.BooleanField(verbose_name="Является начальным")
    is_final = models.BooleanField(verbose_name="Является последним")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Пользовательский статус"
        verbose_name_plural = "Пользовательские статусы"

    def __str__(self):
        return self.name


class StatusGroup(models.Model):
    order = models.IntegerField(verbose_name="Порядковый номер", default=0)
    name = models.CharField(verbose_name="Название", max_length=500)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.RESTRICT)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Пользовательская группа статусов"
        verbose_name_plural = "Пользовательские группы статусов"

    def __str__(self):
        return "%s (%s)" % (self.name, self.user.username)

    @property
    def display_name(self):
        return self.name