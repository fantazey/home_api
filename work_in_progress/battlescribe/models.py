from django.db import models


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
