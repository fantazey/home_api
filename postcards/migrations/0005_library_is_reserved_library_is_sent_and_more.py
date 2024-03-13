# Generated by Django 4.1.5 on 2024-03-04 11:02

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('postcards', '0004_postcard_date_receiving'),
    ]

    operations = [
        migrations.AddField(
            model_name='library',
            name='is_reserved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='library',
            name='is_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='postcard',
            name='date_receiving',
            field=models.DateField(default=datetime.date(2024, 3, 4), verbose_name='дата получения открытки'),
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='ФИО получателя')),
                ('address', models.CharField(max_length=70, verbose_name='адрес получутеля')),
                ('postcode', models.CharField(max_length=8, verbose_name='индекс')),
                ('postcard', models.OneToOneField(on_delete=django.db.models.deletion.RESTRICT, to='postcards.library')),
            ],
        ),
    ]