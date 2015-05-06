# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0002_supplieddata_current_app'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplieddata',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='supplieddata',
            name='form_name',
            field=models.CharField(null=True, choices=[('upload_form', 'File upload'), ('url_form', 'Downloaded from URL'), ('text_form', 'Pasted into textarea')], max_length=20),
        ),
        migrations.AddField(
            model_name='supplieddata',
            name='modified',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
