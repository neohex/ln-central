# Generated by Django 2.2.9 on 2020-02-05 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lner', '0014_invoice_saves_action_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerifyMessageResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memo', models.CharField(max_length=1000, verbose_name='LN Invoice memo')),
                ('valid', models.BooleanField(verbose_name="Is message valid against it's signature?")),
                ('identity_pubkey', models.CharField(max_length=255, verbose_name='LN Identity Pubkey')),
            ],
            options={
                'managed': False,
            },
        ),
    ]
