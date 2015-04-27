# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datainput.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SuppliedData',
            fields=[
                ('uuid', models.CharField(default=datainput.models.make_uuid, primary_key=True, editable=False, serialize=False, max_length=36)),
                ('original_data', models.FileField(upload_to='')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
