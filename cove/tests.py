import pytest
import cove.views as v
import os
import json
from cove.input.models import SuppliedData
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile


def test_get_releases_aggregates():
    assert v.get_releases_aggregates({}) == {
        'count': 0,
        'unique_ocids': [],
        'earliest_release_date': None,
        'latest_release_date': None
    }
    assert v.get_releases_aggregates({'releases': []}) == {
        'count': 0,
        'unique_ocids': set([]),
        'earliest_release_date': None,
        'latest_release_date': None
    }
    assert v.get_releases_aggregates({'releases': [{}, {}, {}]}) == {
        'count': 3,
        'unique_ocids': set([]),
        'earliest_release_date': None,
        'latest_release_date': None
    }


def test_get_file_type_xlsx():
    with open(os.path.join('cove', 'fixtures', 'basic.xlsx')) as fp:
        assert v.get_file_type(UploadedFile(fp, 'basic.xlsx')) == 'xlsx'


def test_get_file_type_csv():
    assert v.get_file_type(SimpleUploadedFile('test.csv', b'a,b')) == 'csv'


def test_get_file_type_json():
    assert v.get_file_type(SimpleUploadedFile('test.json', b'{}')) == 'json'


def test_get_file_type_json_noextension():
    assert v.get_file_type(SimpleUploadedFile('test', b'{}')) == 'json'


def test_get_file_unrecognised_file_type():
    with pytest.raises(v.UnrecognisedFileType):
        v.get_file_type(SimpleUploadedFile('test', b'test'))


def test_get_schema_validation_errors():
    schema_url = 'http://ocds.open-contracting.org/standard/r/1__0__RC/release-package-schema.json'
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases.json')) as fp:
        error_list = v.get_schema_validation_errors(json.load(fp), schema_url)
        assert len(error_list) == 0
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases_invalid.json')) as fp:
        error_list = v.get_schema_validation_errors(json.load(fp), schema_url)
        assert len(error_list) > 0


@pytest.mark.django_db
@pytest.mark.parametrize('current_app', ['cove-ocds', 'cove-360'])
def test_explore_page(client, current_app):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile('{}'))
    data.current_app = current_app
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert resp.context['conversion'] == 'flatten'
    assert 'converted_file_size' in resp.context
    if current_app == 'cove-360':
        assert 'converted_file_size_titles' in resp.context
    else:
        assert 'converted_file_size_titles' not in resp.context


@pytest.mark.django_db
def test_explore_page_csv(client):
    data = SuppliedData.objects.create()
    data.original_file.save('test.csv', ContentFile('a,b'))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert resp.context['conversion'] == 'unflatten'
    assert resp.context['converted_file_size'] == 20


@pytest.mark.django_db
def test_explore_not_json(client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases_not_json.json')) as fp:
        data.original_file.save('test.json', UploadedFile(fp))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert b'not well formed JSON' in resp.content


@pytest.mark.django_db
def test_explore_unconvertable_spreadsheet(client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove', 'fixtures', 'basic.xlsx'), 'rb') as fp:
        data.original_file.save('basic.xlsx', UploadedFile(fp))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert b'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.' in resp.content


@pytest.mark.django_db
def test_explore_unconvertable_json(client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove', 'fixtures', 'unconvertable_json.json')) as fp:
        data.original_file.save('unconvertable_json.json', UploadedFile(fp))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert b'could not be converted' in resp.content
