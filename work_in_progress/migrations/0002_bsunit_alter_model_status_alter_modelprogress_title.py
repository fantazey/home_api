# Generated by Django 4.1.5 on 2023-01-04 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('work_in_progress', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BSUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, verbose_name='Название')),
            ],
        ),
        migrations.AlterField(
            model_name='model',
            name='status',
            field=models.CharField(choices=[('wished', 'Лежит в магазине'), ('in_inventory', 'Лежит в шкафу'), ('assembling', 'Собирается'), ('assembled', 'Собрано'), ('priming', 'Грунтуется'), ('primed', 'Загрунтовано'), ('battle_ready_painting', 'Крашу в базу'), ('battle_ready_painted', 'Покрасил в базу'), ('parade_ready_painting', 'Хайлайтю'), ('parade_ready_painted', 'Добавлены хайхлайты'), ('base_decorating', 'Оформляю поставку'), ('base_decorated', 'База оформлена'), ('varnishing', 'Задуваю лаком'), ('done', 'Закончено')], default='wished', max_length=200, verbose_name='Статус'),
        ),
        migrations.AlterField(
            model_name='modelprogress',
            name='title',
            field=models.CharField(max_length=500, verbose_name='Проводимые работы'),
        ),
    ]
