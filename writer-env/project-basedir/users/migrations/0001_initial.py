# Generated by Django 2.1.7 on 2019-03-21 18:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pubkey', models.CharField(db_index=True, max_length=255, unique=True, verbose_name='LN Identity Pubkey')),
                ('type', models.IntegerField(choices=[(0, 'User'), (1, 'Moderator'), (2, 'Admin'), (3, 'Blog')], default=0)),
                ('status', models.IntegerField(choices=[(0, 'New User'), (1, 'Trusted'), (2, 'Suspended'), (3, 'Banned')], default=0)),
                ('new_messages', models.IntegerField(default=0)),
                ('badges', models.IntegerField(default=0)),
                ('score', models.IntegerField(default=0)),
                ('activity', models.IntegerField(default=0)),
                ('flair', models.CharField(default='', max_length=15, verbose_name='Flair')),
                ('site', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='sites.Site')),
            ],
        ),
    ]
