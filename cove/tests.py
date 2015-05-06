import pytest
import cove.views as v
import os
from cove.input.models import SuppliedData
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile


def test_get_releases_aggregates():
    assert v.get_releases_aggregates({}) == {
        'count': 0,
        'unique_ocids': []
    }
    assert v.get_releases_aggregates({'releases': []}) == {
        'count': 0,
        'unique_ocids': set([])
    }
    assert v.get_releases_aggregates({'releases': [{}, {}, {}]}) == {
        'count': 3,
        'unique_ocids': set([])
    }


def test_get_file_type_xlsx():
    with open(os.path.join('cove', 'fixtures', 'basic.xlsx')) as fp:
        assert v.get_file_type(UploadedFile(fp, 'basic.xlsx')) == 'xlsx'


def test_get_file_type_json():
    assert v.get_file_type(SimpleUploadedFile('test.json', b'{}')) == 'json'


def test_get_file_type_json_noextension():
    assert v.get_file_type(SimpleUploadedFile('test', b'{}')) == 'json'


def test_get_file_unrecognised_file_type():
    with pytest.raises(v.UnrecognisedFileType):
        v.get_file_type(SimpleUploadedFile('test', b'test'))


@pytest.mark.django_db
def test_explore_page(client):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile('{}'))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
