# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dataload', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('process', models.CharField(max_length=20)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('successful', models.BooleanField(default=True)),
                ('dataset', models.ForeignKey(to='dataload.Dataset')),
            ],
        ),
        migrations.RemoveField(
            model_name='process',
            name='dataset',
        ),
        migrations.DeleteModel(
            name='Process',
        ),
    ]
