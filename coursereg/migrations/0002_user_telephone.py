# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-14 12:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coursereg', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='telephone',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
