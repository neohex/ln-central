# Generated by Django 2.2.9 on 2020-02-16 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20191231_2235'),
    ]

    operations = [
        migrations.AddField(
            model_name='postpreview',
            name='parent_post_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]