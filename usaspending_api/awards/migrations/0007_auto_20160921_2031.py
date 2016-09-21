# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-21 20:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('references', '0008_auto_20160920_2000'),
        ('awards', '0006_auto_20160920_1408'),
    ]

    operations = [
        migrations.AddField(
            model_name='financialassistanceaward',
            name='awarding_agency',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='references.Agency'),
        ),
        migrations.AddField(
            model_name='financialassistanceaward',
            name='description',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='financialassistanceaward',
            name='recipient',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='references.LegalEntity'),
        ),
        migrations.AddField(
            model_name='procurement',
            name='awarding_agency',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='references.Agency'),
        ),
        migrations.AddField(
            model_name='procurement',
            name='description',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='procurement',
            name='recipient',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='references.LegalEntity'),
        ),
    ]
