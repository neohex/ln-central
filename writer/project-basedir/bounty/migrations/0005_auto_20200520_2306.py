# Generated by Django 2.2.11 on 2020-05-20 23:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bounty', '0004_auto_20200513_1509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bounty',
            name='award_time',
            field=models.DateTimeField(null=True, verbose_name='award_time is when the winner will be announced'),
        ),
    ]
