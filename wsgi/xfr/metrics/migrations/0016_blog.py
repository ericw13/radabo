# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-07-28 12:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metrics', '0015_auto_20160721_1554'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.CharField(max_length=1000)),
                ('noteType', models.CharField(choices=[('I', 'Informational'), ('R', 'Release Notes'), ('W', 'Warnings')], max_length=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
