# Generated by Django 2.2.9 on 2019-12-31 22:35

import common.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_delete_emailsub'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='content',
            field=models.TextField(default='', validators=[common.validators.validate_signable_field]),
        ),
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=200, validators=[common.validators.validate_signable_field]),
        ),
        migrations.AlterField(
            model_name='postpreview',
            name='content',
            field=models.TextField(default='', validators=[common.validators.validate_signable_field]),
        ),
        migrations.AlterField(
            model_name='postpreview',
            name='memo',
            field=models.CharField(max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='postpreview',
            name='title',
            field=models.CharField(max_length=200, validators=[common.validators.validate_signable_field]),
        ),
    ]
