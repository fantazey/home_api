# Generated by Django 4.1.5 on 2023-01-07 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('work_in_progress', '0008_model_hidden'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelprogress',
            name='status',
            field=models.CharField(choices=[('wished', 'Лежит в магазине'), ('in_inventory', 'Лежит в шкафу'), ('assembling', 'Собирается'), ('assembled', 'Собрано'), ('priming', 'Грунтуется'), ('primed', 'Загрунтовано'), ('battle_ready_painting', 'Крашу в базу'), ('battle_ready_painted', 'Покрасил в базу'), ('parade_ready_painting', 'Хайлайтю'), ('parade_ready_painted', 'Добавлены хайхлайты'), ('base_decorating', 'Оформляю поставку'), ('base_decorated', 'База оформлена'), ('varnishing', 'Задуваю лаком'), ('done', 'Закончено')], max_length=200, null=True, verbose_name='Статус'),
        ),
    ]
