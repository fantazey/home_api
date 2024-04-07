import datetime
from os import path

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from home_api.settings import DEBUG


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


class BSCategory(models.Model):
    """
    Категория прочитананя из каталога данных BattleScribe
    """
    name = models.CharField(verbose_name="Название", max_length=500)
    source = models.CharField(verbose_name="Источник", max_length=500)

    class Meta:
        verbose_name = "Категория BattleScribe"
        verbose_name_plural = "Категории BattleScribe"

    def __str__(self):
        return "%s(%s)" % (self.name, self.source)

    def __unicode__(self):
        return "%s(%s)" % (self.name, self.source)


class BSUnit(models.Model):
    """
    Юнит прочитанный из каталога BattleScribe
    """
    name = models.CharField(verbose_name="Название", max_length=500)
    bs_category = models.ForeignKey(BSCategory, on_delete=models.RESTRICT, verbose_name="Тип", null=True)

    class Meta:
        verbose_name = "Юнит BattleScribe"
        verbose_name_plural = "Юниты BattleScribe"

    def __str__(self):
        return "%s (%s)" % (self.name, self.bs_category.name)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.bs_category.name)


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
        return "%s - %s" % (self.name, self.get_status_display())

    def __unicode__(self):
        return "%s - %s" % (self.name, self.get_status_display())

    def _update_status(self, new_status, progress_title):
        progress = ModelProgress(model=self,
                                 datetime=datetime.datetime.now(),
                                 title=progress_title,
                                 status=self.status)
        progress.save()
        self.status = new_status
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

    def change_status(self, status):
        res = list(filter(lambda x: x[0] == status, Model.stages()))
        if len(res) > 0:
            self._update_status(res[0][0], res[0][1])

    def put_in_inventory(self):
        self.buy_date = datetime.datetime.now()
        self._update_status(self.Status.IN_INVENTORY, "Куплено")

    def start_assembly(self):
        self._update_status(self.Status.ASSEMBLING, "Начал сборку")

    def finish_assembly(self):
        self._update_status(self.Status.ASSEMBLED, "Закончил сборку")

    def start_priming(self):
        self._update_status(self.Status.PRIMING, "Начал грунтовать")

    def finish_priming(self):
        self._update_status(self.Status.PRIMED, "Загрунтовано")

    def start_painting(self):
        self._update_status(self.Status.BATTLE_READY_PAINTING, "Начал красить в базу")

    def finish_painting(self):
        self._update_status(self.Status.BATTLE_READY_PAINTED, "Покрасил в базу")

    def start_parade_ready_painting(self):
        self._update_status(self.Status.PARADE_READY_PAINTING, "Начал добавлять хайлайты")

    def finish_parade_ready_painting(self):
        self._update_status(self.Status.PARADE_READY_PAINTED, "Законил хайлайты")

    def start_base_decoration(self):
        self._update_status(self.Status.BASE_DECORATING, "Начал оформлять подставки")

    def finish_base_decoration(self):
        self._update_status(self.Status.BASE_DECORATED, "Подставки оформлены")

    def start_varnishing(self):
        self._update_status(self.Status.VARNISHING, "Начал задувать лаком")

    def finish_varnishing(self):
        self._update_status(self.Status.DONE, "Готово!")

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


class Artist(models.Model):
    user = models.OneToOneField(User, verbose_name="Пользователь", on_delete=models.RESTRICT)
    telegram_name = models.CharField(verbose_name="Ник в телеге", max_length=200, unique=True)

    class Meta:
        verbose_name = "Красильщик"
        verbose_name_plural = "Красильщики"

    def __str__(self):
        return self.user.username


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


class KillTeam(models.Model):
    name = models.CharField(verbose_name="Название", max_length=500)

    class Meta:
        verbose_name = "Истребительная команда"
        verbose_name_plural = "Истребительная команда"

    def __str__(self):
        return self.name


class KillTeamOperative(models.Model):
    kill_team = models.ForeignKey(KillTeam, verbose_name="Команда", on_delete=models.RESTRICT)
    name = models.CharField(verbose_name="Название", max_length=500)

    class Meta:
        verbose_name = "Оперативник"
        verbose_name_plural = "Оперативники"

    def __str__(self):
        return self.name
