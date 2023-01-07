# Generated by Django 4.1.5 on 2023-01-06 10:53

from django.db import migrations, models
import django.db.models.deletion
import work_in_progress.models


class Migration(migrations.Migration):

    dependencies = [
        ('work_in_progress', '0006_alter_model_buy_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=work_in_progress.models.model_image_path, verbose_name='Фоточька')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='work_in_progress.model', verbose_name='Модель')),
                ('progress', models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, to='work_in_progress.modelprogress', verbose_name='Процесс покраса')),
            ],
        ),
    ]