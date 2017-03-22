# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dataload', '0004_dataset_deleted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataset',
            name='supplied_data',
        ),
        migrations.RemoveField(
            model_name='processrun',
            name='dataset',
        ),
        migrations.DeleteModel(
            name='Dataset',
        ),
        migrations.DeleteModel(
            name='ProcessRun',
        ),
    ]
