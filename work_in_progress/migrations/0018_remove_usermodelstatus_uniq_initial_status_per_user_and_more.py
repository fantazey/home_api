# Generated by Django 4.1.5 on 2024-10-21 15:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('work_in_progress', '0017_usermodelstatus_slug_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='usermodelstatus',
            name='uniq_initial_status_per_user',
        ),
        migrations.RemoveConstraint(
            model_name='usermodelstatus',
            name='uniq_final_status_per_user',
        ),
    ]
