# Generated by Django 2.2.9 on 2020-02-14 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lner', '0017_rename_identity_pubkey_to_node_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='lightningnode',
            name='qos_score',
            field=models.IntegerField(default=-1, verbose_name='Higher score means higher quality of service'),
        ),
    ]
