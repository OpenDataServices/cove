# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplieddata',
            name='current_app',
            field=models.CharField(default='cove-ocds', max_length=20),
            preserve_default=False,
        ),
    ]
