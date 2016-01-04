# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0004_auto_20150908_1533'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplieddata',
            name='source_url',
            field=models.URLField(null=True, max_length=2000),
        ),
    ]
