# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-29 20:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('edc_call_manager', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='call',
            old_name='last_called',
            new_name='call_datetime',
        ),
        migrations.RenameField(
            model_name='historicalcall',
            old_name='last_called',
            new_name='call_datetime',
        ),
    ]