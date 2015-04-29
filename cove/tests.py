import pytest
import requests
import cove.views as v
from cove.input.models import SuppliedData
from django.core.files.base import ContentFile


def test_get_releases_aggregates():
    assert v.get_releases_aggregates({}) == {
        'count': 0
    }
    assert v.get_releases_aggregates({'releases': []}) == {
        'count': 0
    }
    assert v.get_releases_aggregates({'releases': [{}, {}, {}]}) == {
        'count': 3
    }


def test_get_file_type_xlsx(rf):
    r = requests.get('https://raw.githubusercontent.com/OpenDataServices/flatten-tool/master/flattentool/tests/fixtures/xlsx/basic.xlsx')
    django_file = ContentFile(r.content)
    django_file.name = 'basic.xlsx'
    assert v.get_file_type(django_file) == 'xlsx'


def test_get_file_type_json(rf):
    django_file = ContentFile(b'{}')
    django_file.name = 'test.json'
    assert v.get_file_type(django_file) == 'json'


def test_get_file_type_json_noextension(rf):
    django_file = ContentFile(b'{}')
    django_file.name = 'test'
    assert v.get_file_type(django_file) == 'json'


@pytest.mark.django_db
def test_input_post(rf):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile('{}'))
    v.explore(rf.get('/pk/{}'.format(data.pk)), str(data.pk))
