from django.core.management import call_command
from cove.input.models import SuppliedData
from django.core.files.base import ContentFile
import pytest
import os
from django.utils import timezone


@pytest.mark.django_db
def test_expire_files():
    recent = SuppliedData.objects.create()
    recent.original_file.save('test.json', ContentFile('{}'))

    old = SuppliedData.objects.create()
    old.created = timezone.datetime(2015, 1, 1)
    old.original_file.save('test.json', ContentFile('{}'))

    call_command('expire_files')
    assert os.path.exists(recent.upload_dir())
    assert not os.path.exists(old.upload_dir())
