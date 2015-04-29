import pytest
import cove.views as v
from cove.input.models import SuppliedData
from django.core.files.base import ContentFile

def test_get_releases_aggregates():
    assert v.get_releases_aggregates({}) == {
        'count': 0
    }
    assert v.get_releases_aggregates({ 'releases': [] }) == {
        'count': 0
    }
    assert v.get_releases_aggregates({ 'releases': [{}, {}, {}] }) == {
        'count': 3
    }

@pytest.mark.django_db
def test_input_post(rf):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile('{}'))
    resp = v.explore(rf.get('/pk/{}'.format(data.pk)), str(data.pk))
