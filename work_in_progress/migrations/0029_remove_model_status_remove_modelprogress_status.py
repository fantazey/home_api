# Generated by Django 4.1.5 on 2024-11-18 17:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('work_in_progress', '0028_remove_model_group_model_groups'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='model',
            name='status',
        ),
        migrations.RemoveField(
            model_name='modelprogress',
            name='status',
        ),
    ]
