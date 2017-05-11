# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0006_supplieddata_rendered'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplieddata',
            name='schema_version',
            field=models.CharField(max_length=10, default=''),
        ),
        migrations.AlterField(
            model_name='supplieddata',
            name='rendered',
            field=models.BooleanField(default=False),
        ),
    ]
