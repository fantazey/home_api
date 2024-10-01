from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    name = models.CharField(verbose_name="Название задачи", max_length=400)
    assigned = models.ForeignKey(User, verbose_name="Исполнитель", on_delete=models.RESTRICT, null=True)
    created = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    related_place = models.CharField(verbose_name="Связанное место", max_length=400)
    address = models.CharField(verbose_name="Адрес точки", max_length=400)
    activity = models.IntegerField(verbose_name="Мероприятие")

    class Meta:
        ordering = ["created"]
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"


class CheckList(models.Model):
    task = models.ForeignKey(Task, on_delete=models.RESTRICT)

    class Meta:
        ordering = ["id"]
        verbose_name = "Чеклист"
        verbose_name_plural = "Чеклисты"


class CheckListItem(models.Model):
    work = models.CharField(verbose_name="Работы", max_length=400)
    unit = models.CharField(verbose_name="Единицы измерения", max_length=400)
    count = models.IntegerField(verbose_name="Количество")
    check_list = models.ForeignKey(CheckList, on_delete=models.RESTRICT, related_name='items')

    class Meta:
        ordering = ["id"]
        verbose_name = "Запись чеклиста"
        verbose_name_plural = "Записи чеклиста"


def image_path(instance: 'CheckListItemImage', filename: str):
    return "todo/%s/%s/%s" % (instance.check_list_item.check_list.id,
                              instance.check_list_item.check_list.task.id,
                              filename)


class CheckListItemImage(models.Model):
    image = models.ImageField(verbose_name="Изображение", upload_to=image_path)
    created = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    check_list_item = models.ForeignKey(CheckListItem, on_delete=models.RESTRICT)

    def __str__(self):
        return "%s %s" % (self.check_list_item.work, self.created.strftime("%y-%m-%d %H:%M:%S"))

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"
