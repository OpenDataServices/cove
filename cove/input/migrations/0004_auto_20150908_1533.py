# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cove.input.models


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0003_auto_20150506_1649'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplieddata',
            name='original_file',
            field=models.FileField(upload_to=cove.input.models.upload_to),
        ),
    ]
