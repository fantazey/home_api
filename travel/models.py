from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Place(models.Model):
    name = models.CharField(verbose_name="Название", max_length=300)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.SET_NULL, null=True)
    longitude = models.FloatField(verbose_name="Долгота")
    latitude = models.FloatField(verbose_name="Широта")
    date = models.DateField(verbose_name="Дата посещения")
    rating = models.IntegerField(verbose_name="Оценка", validators=[MinValueValidator(limit_value=0),
                                                                    MaxValueValidator(limit_value=5)])

    class Meta:
        verbose_name = "Посещенное место"
        verbose_name_plural = "Посещенные места"
        ordering = ["-date"]
