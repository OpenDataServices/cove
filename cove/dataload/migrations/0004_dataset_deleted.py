# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataload', '0003_dataset_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
    ]
