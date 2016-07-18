import pytest
import cove.input.views as v
from cove.input.models import SuppliedData
from django.conf import settings


def fake_cove_middleware(request):
    by_namespace = settings.COVE_CONFIG_BY_NAMESPACE
    request.cove_config = {key: by_namespace[key]['default'] for key in by_namespace}
    request.current_app = 'test'
    return request


@pytest.mark.django_db
def test_input(rf):
    resp = v.input(fake_cove_middleware(rf.get('/')))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_input_post(rf):
    resp = v.input(fake_cove_middleware(rf.post('/', {
        'source_url': 'https://raw.githubusercontent.com/OpenDataServices/flatten-tool/master/flattentool/tests/fixtures/tenders_releases_2_releases.json'
    })))
    assert resp.status_code == 302
    assert SuppliedData.objects.count() == 1
    data = SuppliedData.objects.first()
    assert resp.url.endswith(str(data.pk))


@pytest.mark.django_db
def test_connection_error(rf):
    resp = v.input(fake_cove_middleware(rf.post('/', {
        'source_url': 'http://localhost:1234'
    })))
    assert b'Connection refused' in resp.content

    resp = v.input(fake_cove_middleware(rf.post('/', {
        'source_url': 'https://wrong.host.badssl.com/'
    })))
    assert b'doesn\'t match either of' in resp.content
