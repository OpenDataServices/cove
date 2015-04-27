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
                ('uuid', models.CharField(primary_key=True, default=datainput.models.make_uuid, editable=False, max_length=36, serialize=False)),
                ('source_url', models.URLField(null=True)),
                ('original_file', models.FileField(upload_to='')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
