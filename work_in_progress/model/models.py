import datetime
from os import path

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from home_api.settings import DEBUG
from work_in_progress.battlescribe.models import BSUnit
from work_in_progress.manage.models import UserModelStatus


class Model(models.Model):
    """
    Модель над которой идет работа. Может состоять из одной или нескольких миниатюр. Считаем что модель это коробка
    """
    class Status(models.TextChoices):
        """
        Статусы через которые проходит модель в процессе работы над ней
        """
        WISHED = 'wished', 'Лежит в магазине'
        IN_INVENTORY = 'in_inventory', 'Лежит в шкафу'
        ASSEMBLING = 'assembling', 'Собирается'
        ASSEMBLED = 'assembled', 'Собрано'
        PRIMING = 'priming', 'Грунтуется'
        PRIMED = 'primed', 'Загрунтовано'
        BATTLE_READY_PAINTING = 'battle_ready_painting', 'Крашу в базу'
        BATTLE_READY_PAINTED = 'battle_ready_painted', 'Покрасил в базу'
        PARADE_READY_PAINTING = 'parade_ready_painting', 'Хайлайтю'
        PARADE_READY_PAINTED = 'parade_ready_painted', 'Добавлены хайхлайты'
        BASE_DECORATING = 'base_decorating', 'Оформляю поставку'
        BASE_DECORATED = 'base_decorated', 'База оформлена'
        VARNISHING = 'varnishing', 'Задуваю лаком'
        DONE = 'done', 'Закончено'

        @staticmethod
        def work_order():
            return [
                Model.Status.WISHED, Model.Status.IN_INVENTORY,
                Model.Status.ASSEMBLING, Model.Status.ASSEMBLED,
                Model.Status.PRIMING, Model.Status.PRIMED,
                Model.Status.BATTLE_READY_PAINTING, Model.Status.BATTLE_READY_PAINTED,
                Model.Status.PARADE_READY_PAINTING, Model.Status.PARADE_READY_PAINTED,
                Model.Status.BASE_DECORATING, Model.Status.BASE_DECORATED,
                Model.Status.VARNISHING, Model.Status.DONE,
            ]

    name = models.CharField(verbose_name="Название модели", max_length=500)
    battlescribe_unit = models.ForeignKey(BSUnit, verbose_name="Из каталога BS", on_delete=models.RESTRICT, null=True)
    kill_team = models.ForeignKey('KillTeam', verbose_name="KillTeam каталога BS", on_delete=models.RESTRICT, null=True)
    status = models.CharField(verbose_name="Статус", max_length=200, choices=Status.choices, default=Status.WISHED)
    user_status = models.ForeignKey('UserModelStatus', on_delete=models.RESTRICT, verbose_name="Статус",
                                    related_name="model_status", null=True)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.RESTRICT)
    buy_date = models.DateField(verbose_name="Дата покупки", null=True)
    created = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    updated = models.DateTimeField(verbose_name="Дата обновления", auto_now=True)
    hidden = models.BooleanField(verbose_name="Скрыто", default=False)
    unit_count = models.IntegerField(verbose_name="Количество миниатюр", default=1, null=True, blank=True,
                                     validators=[MinValueValidator(limit_value=1)])
    terrain = models.BooleanField(verbose_name="Террейн", default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "Модель в работе"
        verbose_name_plural = "Модели в работе"

    def __str__(self):
        return "%s - %s" % (self.name, self.user_status.name)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.user_status.name)

    def _update_status(self, new_status: 'UserModelStatus'):
        if self.user != new_status.user:
            raise Exception("Пользователь модели и статуса не совпадает")
        progress = ModelProgress(model=self,
                                 datetime=datetime.datetime.now(),
                                 title=new_status.transition_title,
                                 user_status=new_status)
        progress.save()
        self.user_status = new_status
        self.save()

    @staticmethod
    def stages() -> list[tuple[Status, str]]:
        return [
            (Model.Status.IN_INVENTORY, "Куплено"),
            (Model.Status.ASSEMBLING, "Начал сборку"),
            (Model.Status.ASSEMBLED, "Закончил сборку"),
            (Model.Status.PRIMING, "Начал грунтовать"),
            (Model.Status.PRIMED, "Загрунтовано"),
            (Model.Status.BATTLE_READY_PAINTING, "Начал красить в базу"),
            (Model.Status.BATTLE_READY_PAINTED, "Покрасил в базу"),
            (Model.Status.PARADE_READY_PAINTING, "Начал добавлять хайлайты"),
            (Model.Status.PARADE_READY_PAINTED, "Законил хайлайты"),
            (Model.Status.BASE_DECORATING, "Начал оформлять подставки"),
            (Model.Status.BASE_DECORATED, "Подставки оформлены"),
            (Model.Status.VARNISHING, "Начал задувать лаком"),
            (Model.Status.DONE, "Готово"),
        ]

    def change_status(self, status: str):
        user_status = UserModelStatus.objects.get(user=self.user, slug=status)
        self._update_status(user_status)

    @property
    def get_days_since_buy(self):
        if self.buy_date:
            return (datetime.datetime.now().date() - self.buy_date).days
        return "хз скока"

    @property
    def get_hours_spent(self):
        return self.progress.aggregate(models.Sum("time"))["time__sum"] or 0

    @property
    def get_last_image(self):
        if not self.modelimage_set.exists():
            return None
        image = self.modelimage_set.order_by("-id").first().image
        if DEBUG and not path.exists(image.path):
            return None
        return image

    @property
    def get_last_image_url(self):
        if self.get_last_image:
            return self.get_last_image.url
        return None

    @property
    def get_last_image_preview_size(self):
        ratio = self.get_last_image.width / self.get_last_image.height
        return {
            "width": 100,
            "height": 100 / ratio
        }


class ModelProgress(models.Model):
    """
        Запись о работе над моделью
    """
    title = models.CharField(verbose_name="Проводимые работы", max_length=500)
    description = models.TextField(verbose_name="Подробности выполнененной работы")
    datetime = models.DateTimeField(verbose_name="Дата записи")
    time = models.FloatField(verbose_name="Затраченое время в часах", default=0.0)
    model = models.ForeignKey(Model, on_delete=models.RESTRICT, verbose_name="Прогресс", related_name="progress")
    status = models.CharField(verbose_name="Статус", max_length=200, choices=Model.Status.choices, null=True)
    user_status = models.ForeignKey('UserModelStatus', on_delete=models.RESTRICT, verbose_name="Статус",
                                    related_name="progress_status", null=True)

    class Meta:
        ordering = ["datetime"]
        verbose_name = "Работа над моделью"
        verbose_name_plural = "Работы над моделью"

    def __str__(self):
        return "%s - %s - %s - %s" % (self.model.name, self.title, self.time, self.datetime)

    def __unicode__(self):
        return "%s - %s - %s - %s" % (self.model.name, self.title, self.time, self.datetime)

    def add_images(self, images):
        for image_file in images:
            image = ModelImage(progress=self, model=self.model, image=image_file)
            image.save()


def model_image_path(instance: 'ModelImage', filename: str):
    return "wip/%s/%s/%s" % (instance.model.user.username, instance.model.name, filename)


class ModelImage(models.Model):
    image = models.ImageField(verbose_name="Фоточька", upload_to=model_image_path)
    progress = models.ForeignKey(ModelProgress, verbose_name="Процесс покраса", null=True, on_delete=models.RESTRICT)
    model = models.ForeignKey(Model, verbose_name="Модель", on_delete=models.RESTRICT)
    created = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    def __str__(self):
        return "%s %s" % (self.model.name, self.created.strftime("%y-%m-%d %H:%M:%S"))

    class Meta:
        verbose_name = "Изображение модели"
        verbose_name_plural = "Изображения модели"