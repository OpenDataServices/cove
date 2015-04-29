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


@pytest.mark.django_db
def test_get_file_type_xlsx(rf):
    r = requests.get('https://raw.githubusercontent.com/OpenDataServices/flatten-tool/master/flattentool/tests/fixtures/xlsx/basic.xlsx')
    assert v.get_file_type(ContentFile(r.content)) == 'xlsx'


def test_get_file_type_json(rf):
    assert v.get_file_type(ContentFile(b'{}')) == 'json'


@pytest.mark.django_db
def test_input_post(rf):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile('{}'))
    v.explore(rf.get('/pk/{}'.format(data.pk)), str(data.pk))
