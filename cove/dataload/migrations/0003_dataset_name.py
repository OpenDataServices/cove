# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataload', '0002_auto_20150928_1719'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='name',
            field=models.CharField(default=None, max_length=50, unique=True),
            preserve_default=False,
        ),
    ]
