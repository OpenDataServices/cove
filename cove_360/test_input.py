import os
import pytest
import cove.input.views as v
from cove.input.models import SuppliedData


def fake_cove_middleware(request):
    request.current_app = 'cove_360'
    request.current_app_base_template = 'cove_360/base.html'
    return request


@pytest.mark.django_db
def test_input(rf):
    resp = v.data_input(fake_cove_middleware(rf.get('/')))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_input_post(rf):
    resp = v.data_input(fake_cove_middleware(rf.post('/', {
        'source_url': 'https://raw.githubusercontent.com/OpenDataServices/flatten-tool/master/flattentool/tests/fixtures/tenders_releases_2_releases.json'
    })))
    assert resp.status_code == 302
    assert SuppliedData.objects.count() == 1
    data = SuppliedData.objects.first()
    assert resp.url.endswith(str(data.pk))


@pytest.mark.django_db
def test_connection_error(rf):
    resp = v.data_input(fake_cove_middleware(rf.post('/', {
        'source_url': 'http://localhost:1234'
    })))
    assert b'Connection refused' in resp.content

    resp = v.data_input(fake_cove_middleware(rf.post('/', {
        'source_url': 'https://wrong.host.badssl.com/'
    })))
    assert b'doesn&#39;t match either of' in resp.content


@pytest.mark.django_db
def test_http_error(rf):
    resp = v.data_input(fake_cove_middleware(rf.post('/', {
        'source_url': 'http://google.co.uk/cove'
    })))
    assert b'Not Found' in resp.content


@pytest.mark.django_db
def test_extension_from_content_type(rf, httpserver):
    httpserver.serve_content('{}', headers={
        'content-type': 'text/csv'
    })
    v.data_input(fake_cove_middleware(rf.post('/', {
        'source_url': httpserver.url
    })))
    supplied_datas = SuppliedData.objects.all()
    assert len(supplied_datas) == 1
    assert supplied_datas[0].original_file.name.endswith('.csv')


@pytest.mark.django_db
def test_extension_from_content_disposition(rf, httpserver):
    httpserver.serve_content('{}', headers={
        'content-disposition': 'attachment; filename="something.csv"'
    })
    v.data_input(fake_cove_middleware(rf.post('/', {
        'source_url': httpserver.url
    })))
    supplied_datas = SuppliedData.objects.all()
    assert len(supplied_datas) == 1
    assert supplied_datas[0].original_file.name.endswith('.csv')


@pytest.mark.django_db
def test_directory_for_empty_filename(rf):
    '''
    Check that URLs ending in / correctly create a directory, to test against
    regressions of https://github.com/OpenDataServices/cove/issues/426
    '''
    v.data_input(fake_cove_middleware(rf.post('/', {
        'source_url': 'http://example.org/'
    })))
    supplied_datas = SuppliedData.objects.all()
    assert len(supplied_datas) == 1
    assert os.path.isdir(supplied_datas[0].upload_dir())
