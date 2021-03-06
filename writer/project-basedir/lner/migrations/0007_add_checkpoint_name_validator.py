# Generated by Django 2.2.9 on 2019-12-28 18:48

from django.db import migrations, models
import common.validators


class Migration(migrations.Migration):

    dependencies = [
        ('lner', '0006_make_checkpoint_name_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoicelistcheckpoint',
            name='checkpoint_name',
            field=models.CharField(default='__DEFAULT__', max_length=255, unique=True, validators=[common.validators.validate_checkpoint_name], verbose_name='Checkpoint name'),
        ),
    ]
