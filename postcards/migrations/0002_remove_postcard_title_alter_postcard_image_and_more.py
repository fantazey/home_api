# Generated by Django 4.1.5 on 2024-02-05 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('postcards', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postcard',
            name='title',
        ),
        migrations.AlterField(
            model_name='postcard',
            name='image',
            field=models.ImageField(upload_to='postcard', verbose_name='лицевая сторона'),
        ),
        migrations.AlterField(
            model_name='postcard',
            name='travel_time',
            field=models.IntegerField(verbose_name='дней в пути'),
        ),
    ]