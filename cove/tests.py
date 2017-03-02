import os
import pytest
import cove.views as v
import cove.lib.common as c
import cove.lib.ocds as ocds
import json
from unittest.mock import patch
from collections import OrderedDict
from cove.input.models import SuppliedData
from cove.lib.converters import convert_json, convert_spreadsheet
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.utils.translation import ugettext_lazy


EMPTY_RELEASE_AGGREGATE = {
    'award_doc_count': 0,
    'award_doctype': {},
    'award_count': 0,
    'contract_doc_count': 0,
    'contract_doctype': {},
    'contract_count': 0,
    'contracts_without_awards': [],
    'duplicate_release_ids': set(),
    'implementation_count': 0,
    'implementation_doc_count': 0,
    'implementation_doctype': {},
    'implementation_milestones_doc_count': 0,
    'implementation_milestones_doctype': {},
    'item_identifier_schemes': set(),
    'max_award_date': '',
    'max_contract_date': '',
    'max_release_date': '',
    'max_tender_date': '',
    'min_award_date': '',
    'min_contract_date': '',
    'min_release_date': '',
    'min_tender_date': '',
    'organisations_with_address': 0,
    'organisations_with_contact_point': 0,
    'planning_doc_count': 0,
    'planning_doctype': {},
    'planning_count': 0,
    'award_item_count': 0,
    'contract_item_count': 0,
    'release_count': 0,
    'tender_item_count': 0,
    'tags': {},
    'tender_doc_count': 0,
    'tender_doctype': {},
    'tender_milestones_doc_count': 0,
    'tender_milestones_doctype': {},
    'tender_count': 0,
    'unique_award_id': set(),
    'unique_buyers_count': 0,
    'unique_buyers_identifier': {},
    'unique_buyers_name_no_id': set(),
    'unique_currency': set(),
    'unique_initation_type': set(),
    'unique_lang': set(),
    'unique_ocids': set(),
    'unique_org_count': 0,
    'unique_org_identifier_count': 0,
    'unique_org_name_count': 0,
    'unique_organisation_schemes': set(),
    'unique_procuring_count': 0,
    'unique_procuring_identifier': {},
    'unique_procuring_name_no_id': set(),
    'unique_suppliers_count': 0,
    'unique_suppliers_identifier': {},
    'unique_suppliers_name_no_id': set(),
    'unique_tenderers_count': 0,
    'unique_tenderers_identifier': {},
    'unique_tenderers_name_no_id': set(),
    'processes_implementation_count': 0,
    'processes_award_count': 0,
    'processes_contract_count': 0,
    'total_item_count': 0,
    'unique_buyers': set(),
    'unique_procuring': set(),
    'unique_suppliers': set(),
    'unique_tenderers': set()
}

EXPECTED_RELEASE_AGGREGATE = {
    'award_count': 2,
    'award_doc_count': 3,
    'award_doctype': {'doctype1': 2, 'doctype2': 1},
    'award_item_count': 2,
    'contract_count': 2,
    'contract_doc_count': 3,
    'contract_doctype': {'doctype1': 2, 'doctype2': 1},
    'contract_item_count': 2,
    'contracts_without_awards': [{'awardID': 'no',
                               'id': '2',
                               'period': {'startDate': '2015-01-02T00:00Z'},
                               'value': {'currency': 'EUR'}}],
    'duplicate_release_ids': set(),
    'implementation_count': 1,
    'implementation_doc_count': 3,
    'implementation_doctype': {'doctype1': 2, 'doctype2': 1},
    'implementation_milestones_doc_count': 3,
    'implementation_milestones_doctype': {'doctype1': 2, 'doctype2': 1},
    'item_identifier_schemes': {'scheme1', 'scheme2'},
    'max_award_date': '2015-01-02T00:00Z',
    'max_contract_date': '2015-01-02T00:00Z',
    'max_release_date': '2015-01-02T00:00Z',
    'max_tender_date': '2015-01-02T00:00Z',
    'min_award_date': '2015-01-01T00:00Z',
    'min_contract_date': '2015-01-01T00:00Z',
    'min_release_date': '2015-01-02T00:00Z',
    'min_tender_date': '2015-01-02T00:00Z',
    'organisations_with_address': 2,
    'organisations_with_contact_point': 2,
    'planning_count': 1,
    'planning_doc_count': 3,
    'planning_doctype': {'doctype1': 2, 'doctype2': 1},
    'release_count': 1,
    'tags': {'planning': 1, 'tender': 1},
    'tender_count': 1,
    'tender_doc_count': 3,
    'tender_doctype': {'doctype1': 2, 'doctype2': 1},
    'tender_item_count': 2,
    'tender_milestones_doc_count': 3,
    'tender_milestones_doctype': {'doctype1': 2, 'doctype2': 1},
    'unique_award_id': {'1', '2'},
    'unique_buyers_count': 1,
    'unique_buyers_identifier': {'1': 'Gov'},
    'unique_buyers_name_no_id': set(),
    'unique_currency': {'EUR', 'YEN', 'USD', 'GBP'},
    'unique_initation_type': {'tender'},
    'unique_lang': {'English'},
    'unique_ocids': {'1'},
    'unique_org_count': 4,
    'unique_org_identifier_count': 2,
    'unique_org_name_count': 2,
    'unique_organisation_schemes': {'a', 'b'},
    'unique_procuring_count': 1,
    'unique_procuring_identifier': {'1': 'Gov'},
    'unique_procuring_name_no_id': set(),
    'unique_suppliers_count': 3,
    'unique_suppliers_identifier': {'2': 'Big corp3'},
    'unique_suppliers_name_no_id': {'Big corp1', 'Big corp2'},
    'unique_tenderers_count': 3,
    'unique_tenderers_identifier': {'2': 'Big corp3'},
    'unique_tenderers_name_no_id': {'Big corp1', 'Big corp2'},
    'processes_implementation_count': 1,
    'processes_award_count': 1,
    'processes_contract_count': 1,
    'total_item_count': 6,
    'unique_buyers': {'Gov (1)'},
    'unique_procuring': {'Gov (1)'},
    'unique_suppliers': {'Big corp3 (2)', 'Big corp2', 'Big corp1'},
    'unique_tenderers': {'Big corp3 (2)', 'Big corp2', 'Big corp1'},
}

EXPECTED_RELEASE_AGGREGATE_RANDOM = {
    'award_count': 1477,
    'award_doc_count': 2159,
    'award_item_count': 2245,
    'contract_count': 1479,
    'contract_doc_count': 2186,
    'contract_item_count': 2093,
    'implementation_count': 562,
    'implementation_doc_count': 1140,
    'implementation_milestones_doc_count': 1659,
    'max_award_date': '5137-06-18T19:25:03.403Z',
    'max_contract_date': '5113-08-13T17:04:27.669Z',
    'max_release_date': '5137-06-07T19:44:36.152Z',
    'max_tender_date': '5084-05-16T03:11:56.723Z',
    'min_award_date': '1977-01-18T23:35:50.858Z',
    'min_contract_date': '1970-02-23T13:49:12.592Z',
    'min_release_date': '1970-08-03T00:21:37.491Z',
    'min_tender_date': '1989-03-20T22:29:02.697Z',
    'organisations_with_address': 770,
    'organisations_with_contact_point': 729,
    'planning_count': 339,
    'planning_doc_count': 738,
    'release_count': 1005,
    'tender_count': 467,
    'tender_doc_count': 799,
    'tender_item_count': 770,
    'tender_milestones_doc_count': 1163,
    'unique_buyers_count': 169,
    'unique_org_count': 1339,
    'unique_org_identifier_count': 625,
    'unique_org_name_count': 714,
    'unique_procuring_count': 94,
    'unique_suppliers_count': 812,
    'unique_tenderers_count': 286,
    'processes_award_count': 466,
    'processes_contract_count': 467,
    'processes_implementation_count': 327,
    'total_item_count': 5108,
}


def test_get_releases_aggregates():
    assert ocds.get_releases_aggregates({}) == EMPTY_RELEASE_AGGREGATE
    assert ocds.get_releases_aggregates({'releases': []}) == EMPTY_RELEASE_AGGREGATE
    release_aggregate_3_empty = EMPTY_RELEASE_AGGREGATE.copy()
    release_aggregate_3_empty['release_count'] = 3
    assert ocds.get_releases_aggregates({'releases': [{}, {}, {}]}) == release_aggregate_3_empty

    with open(os.path.join('cove', 'fixtures', 'release_aggregate.json')) as fp:
        data = json.load(fp)

    assert ocds.get_releases_aggregates({'releases': data['releases']}) == EXPECTED_RELEASE_AGGREGATE

    # test if a release is duplicated
    actual = ocds.get_releases_aggregates({'releases': data['releases'] + data['releases']})
    actual_cleaned = {key: actual[key] for key in actual if 'doc' not in key}
    actual_cleaned.pop('contracts_without_awards')

    expected_cleaned = {key: EXPECTED_RELEASE_AGGREGATE[key] for key in EXPECTED_RELEASE_AGGREGATE if 'doc' not in key}
    expected_cleaned['tags'] = {'planning': 2, 'tender': 2}
    expected_cleaned.pop('contracts_without_awards')
    expected_cleaned['release_count'] = 2
    expected_cleaned['duplicate_release_ids'] = set(['1'])

    assert actual_cleaned == expected_cleaned

    with open(os.path.join('cove', 'fixtures', 'samplerubbish.json')) as fp:
        data = json.load(fp)

    actual = ocds.get_releases_aggregates(data)
    actual_cleaned = {key: actual[key] for key in actual if isinstance(actual[key], (str, int, float))}

    assert actual_cleaned == EXPECTED_RELEASE_AGGREGATE_RANDOM

    with open(os.path.join('cove', 'fixtures', 'badfile.json')) as fp:
        data = json.load(fp)

    actual = ocds.get_releases_aggregates(data, ignore_errors=True)

    assert actual == {}


def test_fields_present():
    assert c.get_fields_present({}) == {}
    assert c.get_fields_present({'a': 1, 'b': 2}) == {"/a": 1, "/b": 1}
    assert c.get_fields_present({'a': {}, 'b': 2}) == {'/a': 1, '/b': 1}
    assert c.get_fields_present({'a': {'c': 1}, 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1}
    assert c.get_fields_present({'a': {'c': 1}, 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1}
    assert c.get_fields_present({'a': {'c': {'d': 1}}, 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1, '/a/c/d': 1}
    assert c.get_fields_present({'a': [{'c': 1}], 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1}
    assert c.get_fields_present({'a': {'c': [{'d': 1}]}, 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1, '/a/c/d': 1}
    assert c.get_fields_present({'a': {'c_1': [{'d': 1}]}, 'b_1': 2}) == {'/a': 1, '/a/c_1': 1, '/a/c_1/d': 1, '/b_1': 1}
    assert c.get_fields_present({'a': {'c_1': [{'d': 1}, {'d': 1}]}, 'b_1': 2}) == {'/a': 1, '/a/c_1': 1, '/a/c_1/d': 2, '/b_1': 1}


@pytest.mark.parametrize('file_name', ['basic.xlsx', 'basic.XLSX'])
def test_get_file_type_xlsx(file_name):
    with open(os.path.join('cove', 'fixtures', 'basic.xlsx')) as fp:
        assert v.get_file_type(UploadedFile(fp, file_name)) == 'xlsx'


@pytest.mark.parametrize('file_name', ['test.csv', 'test.CSV'])
def test_get_file_type_csv(file_name):
    assert v.get_file_type(SimpleUploadedFile(file_name, b'a,b')) == 'csv'


def test_get_file_type_json():
    assert v.get_file_type(SimpleUploadedFile('test.json', b'{}')) == 'json'


def test_get_file_type_json_noextension():
    assert v.get_file_type(SimpleUploadedFile('test', b'{}')) == 'json'


def test_get_file_unrecognised_file_type():
    with pytest.raises(v.UnrecognisedFileType):
        v.get_file_type(SimpleUploadedFile('test', b'test'))


def test_get_schema_validation_errors():
    schema_url = 'http://ocds.open-contracting.org/standard/r/1__0__RC/'
    schema_name = 'release-package-schema.json'
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases.json')) as fp:
        error_list = c.get_schema_validation_errors(json.load(fp), schema_url, schema_name, 'cove-ocds', {}, {})
        assert len(error_list) == 0
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases_invalid.json')) as fp:
        error_list = c.get_schema_validation_errors(json.load(fp), schema_url, schema_name, 'cove-ocds', {}, {})
        assert len(error_list) > 0


def test_get_json_data_generic_paths():
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases_with_deprecated_fields.json')) as fp:
        json_data_w_deprecations = json.load(fp)

    generic_paths = c._get_json_data_generic_paths(json_data_w_deprecations)
    assert len(generic_paths.keys()) == 27
    assert generic_paths[('releases', 'buyer', 'name')] == {
        ('releases', 1, 'buyer', 'name'): 'Parks Canada',
        ('releases', 0, 'buyer', 'name'): 'Agriculture & Agrifood Canada'
    }


def test_get_json_data_deprecated_fields():
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases_with_deprecated_fields.json')) as fp:
        json_data_w_deprecations = json.load(fp)

    schema_url = os.path.join('cove', 'fixtures/')
    schema_name = 'release_package_schema_ref_release_schema_deprecated_fields.json'
    deprecated_data_fields = c.get_json_data_deprecated_fields(schema_name, schema_url, json_data_w_deprecations)
    expected_result = OrderedDict([
        ('initiationType', {"paths": ('releases/0', 'releases/1'),
                            "explanation": ('1.1', 'Not a useful field as always has to be tender')}),
        ('quantity', {"paths": ('releases/0/tender/items/0',),
                      "explanation": ('1.1', 'Nobody cares about quantities')})
    ])
    for field_name in expected_result.keys():
        assert field_name in deprecated_data_fields
        assert expected_result[field_name]["paths"] == deprecated_data_fields[field_name]["paths"]
        assert expected_result[field_name]["explanation"] == deprecated_data_fields[field_name]["explanation"]


def test_get_schema_deprecated_paths():
    schema_url = os.path.join('cove', 'fixtures/')
    schema_name = 'release_package_schema_ref_release_schema_deprecated_fields.json'
    deprecated_paths = c._get_schema_deprecated_paths(schema_name, schema_url)
    expected_results = [
        (('releases', 'initiationType'), ('1.1', 'Not a useful field as always has to be tender')),
        (('releases', 'planning',), ('1.1', "Testing deprecation for objects with '$ref'")),
        (('releases', 'tender', 'hasEnquiries'), ('1.1', 'Deprecated just for fun')),
        (('releases', 'contracts', 'items', 'quantity'), ('1.1', 'Nobody cares about quantities')),
        (('releases', 'tender', 'items', 'quantity'), ('1.1', 'Nobody cares about quantities')),
        (('releases', 'awards', 'items', 'quantity'), ('1.1', 'Nobody cares about quantities'))
    ]
    assert len(deprecated_paths) == 6
    for path in expected_results:
        assert path in deprecated_paths


@pytest.mark.django_db
@pytest.mark.parametrize('current_app', ['cove-ocds', 'cove-360'])
def test_explore_page(client, current_app):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile('{}'))
    data.current_app = current_app
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert resp.context['conversion'] == 'flattenable'

    resp = client.post(data.get_absolute_url(), {'flatten': 'true'})
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
    with open(os.path.join('cove', 'fixtures', 'bad.xlsx'), 'rb') as fp:
        data.original_file.save('basic.xlsx', UploadedFile(fp))
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert b'We think you tried to supply a spreadsheet, but we failed to convert it to JSON.' in resp.content


@pytest.mark.django_db
def test_explore_unconvertable_json(client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove', 'fixtures', 'unconvertable_json.json')) as fp:
        data.original_file.save('unconvertable_json.json', UploadedFile(fp))
    resp = client.post(data.get_absolute_url(), {'flatten': 'true'})
    assert resp.status_code == 200
    assert b'could not be converted' in resp.content


@pytest.mark.django_db
@pytest.mark.parametrize('current_app', ['cove-ocds', 'cove-360'])
def test_explore_page_null_tag(client, current_app):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile('{"releases":[{"tag":null}]}'))
    data.current_app = current_app
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('json_data', [
    '{"version": "1.1","releases": [{"ocid": "xx"}]}',
    '{"releases": [{"ocid": "xx"}]}'
])
def test_explore_schema_version(client, json_data):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile(json_data))
    data.current_app = 'cove-ocds'

    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    if 'version' in json_data:
        assert '1.1' in resp.context['schema_url']
        assert resp.context['version_used'] == '1.1'
        assert resp.context['version_used_display'] == '1.1-dev'
        resp = client.post(data.get_absolute_url(), {'version': "1.0"})
        assert resp.status_code == 200
        assert '1__0__2' in resp.context['schema_url']
        assert resp.context['version_used'] == '1.0'
    else:
        assert '1__0__2' in resp.context['schema_url']
        assert resp.context['version_used'] == '1.0'
        assert resp.context['version_used_display'] == '1.0'
        resp = client.post(data.get_absolute_url(), {'version': "1.1"})
        assert resp.status_code == 200
        assert '1.1' in resp.context['schema_url']
        assert resp.context['version_used'] == '1.1'
        assert resp.context['version_used_display'] == '1.1-dev'


@pytest.mark.django_db
def test_wrong_schema_version_in_data(client):
    data = SuppliedData.objects.create()
    data.original_file.save('test.json', ContentFile('{"version": "1.bad", "releases": [{"ocid": "xx"}]}'))
    data.current_app = 'cove-ocds'
    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert resp.context['sub_title'] == ugettext_lazy("Wrong schema version")


@pytest.mark.django_db
@pytest.mark.parametrize(('file_type', 'converter', 'replace_after_post'), [
    ('xlsx', convert_spreadsheet, True),
    ('json', convert_json, False)
])
def test_explore_schema_version_change(client, file_type, converter, replace_after_post):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases.{}'.format(file_type)), 'rb') as fp:
        data.original_file.save('test.{}'.format(file_type), UploadedFile(fp))
    data.current_app = 'cove-ocds'

    with patch('cove.views.{}'.format(converter.__name__), side_effect=converter, autospec=True) as mock_object:
        resp = client.get(data.get_absolute_url())
        args, kwargs = mock_object.call_args
        assert resp.status_code == 200
        assert resp.context['version_used'] == '1.0'
        assert mock_object.called
        assert '1__0__2' in kwargs['schema_url']
        assert kwargs['replace'] is False
        mock_object.reset_mock()

        resp = client.post(data.get_absolute_url(), {'version': '1.1'})
        args, kwargs = mock_object.call_args
        assert resp.status_code == 200
        assert resp.context['version_used'] == '1.1'
        assert mock_object.called
        assert '1.1' in kwargs['schema_url']
        assert kwargs['replace'] is replace_after_post


@pytest.mark.django_db
@patch('cove.views.convert_json', side_effect=convert_json, autospec=True)
def test_explore_schema_version_change_with_json_to_xlsx(mock_object, client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases.json')) as fp:
        data.original_file.save('test.json', UploadedFile(fp))
    data.current_app = 'cove-ocds'

    resp = client.get(data.get_absolute_url())
    args, kwargs = mock_object.call_args
    assert resp.status_code == 200
    assert '1__0__2' in kwargs['schema_url']
    assert kwargs['replace'] is False
    mock_object.reset_mock()

    resp = client.post(data.get_absolute_url(), {'version': '1.1'})
    args, kwargs = mock_object.call_args
    assert resp.status_code == 200
    assert kwargs['replace'] is False
    mock_object.reset_mock()

    # Convert to spreadsheet
    resp = client.post(data.get_absolute_url(), {'flatten': 'true'})
    assert kwargs['replace'] is False
    mock_object.reset_mock()

    # Do replace with version change now that it's been converted once
    resp = client.post(data.get_absolute_url(), {'version': '1.0'})
    args, kwargs = mock_object.call_args
    assert resp.status_code == 200
    assert kwargs['replace'] is True
    mock_object.reset_mock()

    # Do not replace if the version does not changed
    resp = client.post(data.get_absolute_url(), {'version': '1.0'})
    args, kwargs = mock_object.call_args
    assert resp.status_code == 200
    assert kwargs['replace'] is False
    mock_object.reset_mock()

    resp = client.post(data.get_absolute_url(), {'version': '1.1'})
    args, kwargs = mock_object.call_args
    assert resp.status_code == 200
    assert kwargs['replace'] is True
    mock_object.reset_mock()


@pytest.mark.django_db
def test_data_supplied_schema_version(client):
    data = SuppliedData.objects.create()
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases.xlsx'), 'rb') as fp:
        data.original_file.save('test.xlsx', UploadedFile(fp))
    data.current_app = 'cove-ocds'
    
    assert data.schema_version == ''

    resp = client.get(data.get_absolute_url())
    assert resp.status_code == 200
    assert resp.context['version_used'] == '1.0'
    assert SuppliedData.objects.get(id=data.id).schema_version == '1.0'

    resp = client.post(data.get_absolute_url(), {'version': '1.1'})
    assert resp.status_code == 200
    assert resp.context['version_used'] == '1.1'
    assert SuppliedData.objects.get(id=data.id).schema_version == '1.1'
