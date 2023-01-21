import datetime

from django.db import models
from django.contrib.auth.models import User

from home_api.settings import DEBUG


class BSCategory(models.Model):
    """
    Категория прочитананя из каталога данных BattleScribe
    """
    name = models.CharField(verbose_name="Название", max_length=500)
    source = models.CharField(verbose_name="Источник", max_length=500)

    class Meta:
        verbose_name = 'Категория BattleScribe'
        verbose_name_plural = 'Категории BattleScribe'

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
        verbose_name = 'Юнит BattleScribe'
        verbose_name_plural = 'Юниты BattleScribe'

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

    name = models.CharField(verbose_name="Название модели", max_length=500)
    battlescribe_unit = models.ForeignKey(BSUnit, verbose_name="Из каталога BS", on_delete=models.RESTRICT, null=True)
    status = models.CharField(verbose_name="Статус", max_length=200, choices=Status.choices, default=Status.WISHED)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.RESTRICT)
    buy_date = models.DateField(verbose_name="Дата покупки", null=True)
    created = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True, null=False, blank=False)
    updated = models.DateTimeField(verbose_name="Дата обновления", auto_now=True, null=False, blank=False)
    hidden = models.BooleanField(verbose_name="Скрыто", default=False)

    class Meta:
        verbose_name = 'Модель в работе'
        verbose_name_plural = 'Модели в работе'

    def __str__(self):
        return "%s - %s" % (self.name, self.get_status_display())

    def __unicode__(self):
        return "%s - %s" % (self.name, self.get_status_display())

    def _update_status(self, new_status, progress_title):
        progress = ModelProgress(model=self, datetime=datetime.datetime.now(), title=progress_title)
        progress.save()
        self.status = new_status
        self.save()

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
        return 'хз скока'

    @property
    def get_hours_spent(self):
        return self.modelprogress_set.aggregate(models.Sum('time'))['time__sum']

    @property
    def get_last_image(self):
        if DEBUG:
            return None

        if self.modelimage_set.exists():
            return self.modelimage_set.order_by('-id').first().image
        return None

    @property
    def get_last_image_url(self):
        if self.get_last_image:
            return self.get_last_image.url
        return None

    @property
    def get_last_image_preview_size(self):
        ratio = self.get_last_image.width / self.get_last_image.height
        return {
            'width': 100,
            'height': 100 / ratio
        }


class ModelProgress(models.Model):
    """
        Запись о работе над моделью
    """
    title = models.CharField(verbose_name="Проводимые работы", max_length=500)
    description = models.TextField(verbose_name="Подробности выполнененной работы")
    datetime = models.DateTimeField(verbose_name="Дата записи")
    time = models.FloatField(verbose_name="Затраченое время в часах", default=0.0)
    model = models.ForeignKey(Model, on_delete=models.RESTRICT, verbose_name="Прогресс")
    status = models.CharField(verbose_name="Статус", max_length=200, choices=Model.Status.choices, null=True)

    class Meta:
        verbose_name = 'Работа над моделью'
        verbose_name_plural = 'Работы над моделью'

    def __str__(self):
        return "%s - %s - %s - %s" % (self.model.name, self.title, self.time, self.datetime)

    def __unicode__(self):
        return "%s - %s - %s - %s" % (self.model.name, self.title, self.time, self.datetime)

    def add_images(self, images):
        for image_file in images:
            image = ModelImage(progress=self, model=self.model, image=image_file)
            image.save()


def model_image_path(instance: 'ModelImage', filename: str):
    return 'wip/%s/%s/%s' % (instance.model.user.username, instance.model.name, filename)


class ModelImage(models.Model):
    image = models.ImageField(verbose_name="Фоточька", upload_to=model_image_path)
    progress = models.ForeignKey(ModelProgress, verbose_name="Процесс покраса", null=True, on_delete=models.RESTRICT)
    model = models.ForeignKey(Model, verbose_name="Модель", on_delete=models.RESTRICT)
    created = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True, null=False, blank=False)


class Artist(models.Model):
    user = models.OneToOneField(User, verbose_name="Пользователь", on_delete=models.RESTRICT)
    telegram_name = models.CharField(verbose_name="Ник в телеге", max_length=200, unique=True)
