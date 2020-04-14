# Generated by Django 2.2.11 on 2020-04-14 15:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('posts', '0007_auto_20200403_1729'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bounty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField()),
                ('ammount', models.IntegerField(default=-1, verbose_name='ammount in sats of the total award for winning the bounty')),
                ('is_active', models.BooleanField(default=True, verbose_name='is_active, false if the Bounty still can be awarded')),
                ('is_payed', models.BooleanField(default=False, verbose_name='is_payed, true when the winner took custody of the funds')),
                ('activation_time', models.DateTimeField(default=False, verbose_name='activation_time is when the bounty became active most recently')),
                ('award_time', models.DateTimeField(verbose_name='award_time is when the winner was announced')),
                ('post_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posts.Post', verbose_name='post_id of the Question where the bounty is posted')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BountyAward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField()),
                ('bounty_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bounty.Bounty', verbose_name='bounty_id which bounty is awarded')),
                ('post_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posts.Post', verbose_name='post_id which post won the awarded')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
