# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-30 15:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FC15', '0007_passwordreset'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100)),
                ('destin_team', models.CharField(max_length=100)),
                ('message', models.CharField(max_length=500)),
                ('status', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='userinfo',
            name='realname',
            field=models.CharField(default='', max_length=100),
        ),
    ]
