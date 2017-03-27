import json
import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile

from cove.lib.common import get_fields_present, _get_json_data_generic_paths
from cove.lib.exceptions import UnrecognisedFileType
from cove.lib.tools import get_file_type


def test_fields_present():
    assert get_fields_present({}) == {}
    assert get_fields_present({'a': 1, 'b': 2}) == {"/a": 1, "/b": 1}
    assert get_fields_present({'a': {}, 'b': 2}) == {'/a': 1, '/b': 1}
    assert get_fields_present({'a': {'c': 1}, 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1}
    assert get_fields_present({'a': {'c': 1}, 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1}
    assert get_fields_present({'a': {'c': {'d': 1}}, 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1, '/a/c/d': 1}
    assert get_fields_present({'a': [{'c': 1}], 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1}
    assert get_fields_present({'a': {'c': [{'d': 1}]}, 'b': 2}) == {'/a': 1, '/b': 1, '/a/c': 1, '/a/c/d': 1}
    assert get_fields_present({'a': {'c_1': [{'d': 1}]}, 'b_1': 2}) == {'/a': 1, '/a/c_1': 1, '/a/c_1/d': 1, '/b_1': 1}
    assert get_fields_present({'a': {'c_1': [{'d': 1}, {'d': 1}]}, 'b_1': 2}) == {'/a': 1, '/a/c_1': 1, '/a/c_1/d': 2, '/b_1': 1}


@pytest.mark.parametrize('file_name', ['basic.xlsx', 'basic.XLSX'])
def test_get_file_type_xlsx(file_name):
    with open(os.path.join('cove', 'fixtures', 'basic.xlsx')) as fp:
        assert get_file_type(UploadedFile(fp, file_name)) == 'xlsx'


@pytest.mark.parametrize('file_name', ['test.csv', 'test.CSV'])
def test_get_file_type_csv(file_name):
    assert get_file_type(SimpleUploadedFile(file_name, b'a,b')) == 'csv'


def test_get_file_type_json():
    assert get_file_type(SimpleUploadedFile('test.json', b'{}')) == 'json'


def test_get_file_type_json_noextension():
    assert get_file_type(SimpleUploadedFile('test', b'{}')) == 'json'


def test_get_file_unrecognised_file_type():
    with pytest.raises(UnrecognisedFileType):
        get_file_type(SimpleUploadedFile('test', b'test'))


def test_get_json_data_generic_paths():
    with open(os.path.join('cove', 'fixtures', 'tenders_releases_2_releases_with_deprecated_fields.json')) as fp:
        json_data_w_deprecations = json.load(fp)

    generic_paths = _get_json_data_generic_paths(json_data_w_deprecations)
    assert len(generic_paths.keys()) == 27
    assert generic_paths[('releases', 'buyer', 'name')] == {
        ('releases', 1, 'buyer', 'name'): 'Parks Canada',
        ('releases', 0, 'buyer', 'name'): 'Agriculture & Agrifood Canada'
    }
