# Generated by Django 4.1.5 on 2023-01-05 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('work_in_progress', '0005_alter_bscategory_options_alter_bsunit_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='model',
            name='buy_date',
            field=models.DateField(null=True, verbose_name='Дата покупки'),
        ),
    ]
