from django.contrib.auth.models import User
from django.db import models


class PaintVendor(models.Model):
    name = models.CharField(verbose_name="Производитель", max_length=300)

    class Meta:
        verbose_name = "Вендор краски"
        verbose_name_plural = "Вендоры красок"

    def __str__(self):
        return self.name


class Paint(models.Model):
    vendor = models.ForeignKey(PaintVendor, verbose_name="Производитель краски", on_delete=models.PROTECT)
    name = models.CharField(verbose_name="Название краски", max_length=300)
    type = models.CharField(verbose_name="Тип краски", max_length=300, null=True, blank=True)
    details = models.CharField(verbose_name="Доп инфо", max_length=600, null=True, blank=True)
    color = models.CharField(verbose_name="Шеснадцатеричное RGB представление цвета", max_length=25, null=True,
                             blank=True)

    def __str__(self):
        if self.details:
            return "[%s] %s [%s]" % (self.details, self.name, self.type)
        return "%s [%s]" % (self.name, self.type)

    class Meta:
        ordering = ["vendor__name", "type", "details", "name"]
        verbose_name = "Краска"
        verbose_name_plural = "Краски"


class PaintInventory(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.RESTRICT)
    paint = models.ForeignKey(Paint, verbose_name="Краска", on_delete=models.RESTRICT)
    wish = models.BooleanField(verbose_name="Нужна", default=False)
    has = models.BooleanField(verbose_name="Есть", default=False)

    def __str__(self):
        return "%s - %s" % (self.user.username, self.paint)

    class Meta:
        ordering = ["user", "has"]
        verbose_name = "Запас красок"
        verbose_name_plural = "Запасы красок"
