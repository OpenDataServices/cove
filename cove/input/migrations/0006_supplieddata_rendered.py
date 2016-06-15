# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0005_auto_20160104_1208'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplieddata',
            name='rendered',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
