# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0004_auto_20150908_1533'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('supplied_data', models.OneToOneField(to='input.SuppliedData')),
            ],
        ),
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('type', models.CharField(choices=[('fetch', 'Fetch'), ('convert', 'Convert'), ('staging', 'Pushed to staging'), ('live', 'Pushed to live')], max_length=20)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('successful', models.BooleanField(default=True)),
                ('dataset', models.ForeignKey(to='dataload.Dataset')),
            ],
        ),
    ]
