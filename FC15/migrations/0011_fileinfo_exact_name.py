# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-06 07:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FC15', '0010_auto_20171006_1542'),
    ]

    operations = [
        migrations.AddField(
            model_name='fileinfo',
            name='exact_name',
            field=models.CharField(default=models.CharField(default=models.CharField(max_length=255), max_length=255), max_length=255),
        ),
    ]
