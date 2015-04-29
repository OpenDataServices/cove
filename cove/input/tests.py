import pytest
import cove.input.views as v
from cove.input.models import SuppliedData


@pytest.mark.django_db
def test_input(rf):
    resp = v.input(rf.get('/'))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_input_post(rf):
    resp = v.input(rf.post('/', {
        'source_url': 'https://raw.githubusercontent.com/OpenDataServices/flatten-tool/master/flattentool/tests/fixtures/tenders_releases_2_releases.json'
    }))
    assert resp.status_code == 302
    assert SuppliedData.objects.count() == 1
    data = SuppliedData.objects.first()
    assert resp.url.endswith(str(data.pk))
