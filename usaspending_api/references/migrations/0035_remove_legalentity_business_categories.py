# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-11-07 11:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('references', '0034_auto_20191016_1818'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='legalentity',
            name='business_categories',
        ),
    ]
