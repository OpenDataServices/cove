import pytest
import defusedxml.lxml as etree
import json
import lxml.etree
import os
import uuid

from django.core.management import call_command

from .lib import iati


XML_SCHEMA = '''
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="test-element">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:integer"/>
            <xsd:element name="b" type="xsd:decimal" minOccurs="1" maxOccurs="unbounded"/>
            <xsd:element name="c" type="xsd:string" minOccurs="1" maxOccurs="unbounded"/>
            <xsd:element name="d" minOccurs="0" maxOccurs="unbounded">
              <xsd:complexType>
                <xsd:attribute name="test-attr" type="xsd:integer" />
              </xsd:complexType>
            </xsd:element>
            <xsd:element name="e" type="xsd:date" maxOccurs="1"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
'''

INVALID_DATA = '''
    <test-element>
      <a>non-int-a</a>
      <b>2</b>
      <b>FF</b>
      <c>string</c>
      <d test-attr="1"/>
      <d test-attr="non-int-d"/>
      <e>non-date</e>
      <e>string</e>
    </test-element>
'''


@pytest.fixture()
def validated_data():
    def _validated_data(data):
        schema_xml = etree.XML(XML_SCHEMA)
        schema_tree = lxml.etree.XMLSchema(schema_xml)
        data_tree = etree.fromstring(data)
        schema_tree.validate(data_tree)
        return schema_tree
    return _validated_data


def test_lxml_errors_generator(validated_data):
    validated_data = validated_data(INVALID_DATA)
    expected_error_paths = ['/test-element/a',
                            '/test-element/b[2]',
                            '/test-element/d[2]',
                            '/test-element/e[1]',
                            '/test-element/e[2]']
    expected_error_messages = ["Element 'a': 'non-int-a' is not a valid value of the atomic type 'xs:integer'.",
                               "Element 'b': 'FF' is not a valid value of the atomic type 'xs:decimal'.",
                               "Element 'd', attribute 'test-attr': 'non-int-d' is not a valid value of the atomic type 'xs:integer'.",
                               "Element 'e': 'non-date' is not a valid value of the atomic type 'xs:date'.",
                               "Element 'e': This element is not expected."]

    lxml_errors = iati.lxml_errors_generator(validated_data.error_log)
    for error_dict in lxml_errors:
        assert error_dict['path'] in expected_error_paths
        assert error_dict['message'] in expected_error_messages


def test_format_lxml_errors(validated_data):
    validated_data = validated_data(INVALID_DATA)
    lmxl_errors = iati.lxml_errors_generator(validated_data.error_log)
    formatted_lxml_errors = iati.format_lxml_errors(lmxl_errors)
    expected_error_paths = ['/test-element/a',
                            '/test-element/b/1',
                            '/test-element/d/1/@test-attr',
                            '/test-element/e/0',
                            '/test-element/e/1']
    expected_error_values = ['non-int-a',
                             'non-int-d',
                             'FF',
                             'non-date',
                             '']
    expected_error_messages = ["'a' is not a valid value of the atomic type 'xs:integer'.",
                               "'b' is not a valid value of the atomic type 'xs:decimal'.",
                               "'d', attribute 'test-attr' is not a valid value of the atomic type 'xs:integer'.",
                               "'e' is not a valid value of the atomic type 'xs:date'.",
                               "'e': This element is not expected."]

    for error_dict in formatted_lxml_errors:
        assert error_dict['path'] in expected_error_paths
        assert error_dict['value'] in expected_error_values
        assert error_dict['message'] in expected_error_messages


@pytest.mark.parametrize(('file_name', 'bad_xml', 'options', 'output'), [
    ('basic_iati_unordered_invalid_iso_dates.xlsx', False, {}, [
        'basic_iati_unordered_invalid_iso_dates.xlsx',
        'results.json',
        'unflattened.xml'
    ]),
    ('basic_iati_unordered_invalid_iso_dates.xlsx', False, {'exclude_file': True}, [
        'results.json',
        'unflattened.xml'
    ]),
    ('basic_iati_ruleset_errors.xml', False, {}, [
        'basic_iati_ruleset_errors.xml',
        'results.json'
    ]),
    ('bad.xml', True, {}, ['bad.xml']),
])
def test_cove_iaiti_cli_dir_content(file_name, bad_xml, options, output):
    test_dir = str(uuid.uuid4())
    file_path = os.path.join('cove_iati', 'fixtures', file_name)
    output_dir = os.path.join('media', test_dir)
    options['output_dir'] = output_dir

    if bad_xml:
        with pytest.raises(SystemExit):
            call_command('iati_cli', file_path, output_dir=output_dir)
    else:
        call_command('iati_cli', file_path, **options)
        assert sorted(os.listdir(output_dir)) == sorted(output)


def test_cove_iati_cli_delete_option():
    test_dir = str(uuid.uuid4())
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_unordered_valid.csv')
    output_dir = os.path.join('media', test_dir)
    call_command('iati_cli', file_path, output_dir=output_dir)

    with pytest.raises(SystemExit):
            call_command('iati_cli', file_path, output_dir=output_dir)


def test_cove_iati_cli_output():
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_ruleset_errors.xml')
    output_dir = os.path.join('media', str(uuid.uuid4()))
    call_command('iati_cli', file_path, output_dir=output_dir)

    with open(os.path.join(output_dir, 'results.json')) as fp:
        results = json.load(fp)

    assert not results.get('ruleset_errors_openag')

    validation_errors = results.get('validation_errors')
    
    assert validation_errors[0]['description'] == "'recipient-country': This element is not expected, expected is activity-date."
    assert validation_errors[0]['path'] == 'iati-activity/0/recipient-country/0'

    ruleset_errors = results.get('ruleset_errors')
    ruleset_errors.sort(key=lambda i: i['path'])

    assert ruleset_errors[0]['rule'] == 'activity-date[date @type="1"] or activity-date[@type="2"] is expected'
    assert ruleset_errors[0]['message'] == 'Neither activity-date[@type="1"] nor activity-date[@type="2"] have been found'
    assert ruleset_errors[0]['id'] == 'AA-AAA-123123-AA123'
    assert ruleset_errors[0]['path'] == '/iati-activities/iati-activity[1]'

    assert ruleset_errors[1]['rule'] == '@iso-date date must be in iso format and must be today or in the past'
    assert '2200-03-03 must be on or before today' in ruleset_errors[1]['message']
    assert ruleset_errors[1]['id'] == 'AA-AAA-123123-AA123'
    assert ruleset_errors[1]['path'] == '/iati-activities/iati-activity[1]/transaction[2]/transaction-date/@iso-date'


def test_cove_iati_cli_openag_output():
    expected = [{'id': 'AA-AAA-123123-AA123',
                 'message': 'the activity should include at least one location element',
                 'path': '/iati-activities/iati-activity[1]',
                 'rule': 'element is expected'},
                {'id': 'AA-AAA-123123-AA123',
                 'message': '@ref NO-ORGIDS-10000 does not start with a recognised org-ids prefix',
                 'path': '/iati-activities/iati-activity[1]/reporting-org/@ref',
                 'rule': '@ref should have an org-ids prefix'},
                {'id': 'BB-BBB-123123-BB123',
                 'message': 'location/location-id element must have @code attribute',
                 'path': '/iati-activities/iati-activity[2]/location/location-id',
                 'rule': 'element must use @code attribute'},
                {'id': 'BB-BBB-123123-BB123',
                 'message': 'location/location-id element must have @vocabulary attribute',
                 'path': '/iati-activities/iati-activity[2]/location/location-id',
                 'rule': 'element must use @vocabulary attribute'},
                {'id': 'BB-BBB-123123-BB123',
                 'message': '"90" is not a valid value for @vocabulary attribute (it should be "98 or 99")',
                 'path': '/iati-activities/iati-activity[2]/openag:tag/@vocabulary',
                 'rule': 'element must have @vocabulary attribute with code for "maintained by the reporting organisation"'},
                {'id': 'BB-BBB-123123-BB123',
                 'message': '"http://bad.org" is not a valid value for @vocabulary-uri attribute (it should be "http://aims.fao.org/aos/agrovoc/")',
                 'path': '/iati-activities/iati-activity[2]/openag:tag/@vocabulary-uri',
                 'rule': 'element must have @vocabulary-uri attribute with agrovoc uri'},
                {'id': 'BB-BBB-123123-BB123',
                 'message': '@ref NO-ORGIDS-40000 does not start with a recognised org-ids prefix',
                 'path': '/iati-activities/iati-activity[2]/participating-org/@ref',
                 'rule': '@ref should have an org-ids prefix'},
                {'id': 'CC-CCC-789789-CC789',
                 'message': 'openag:tag element must have @code attribute',
                 'path': '/iati-activities/iati-activity[3]/openag:tag',
                 'rule': 'element must have @code attribute'},
                {'id': 'CC-CCC-789789-CC789',
                 'message': 'openag:tag element must have @vocabulary-uri attribute',
                 'path': '/iati-activities/iati-activity[3]/openag:tag',
                 'rule': 'element must have @vocabulary-uri attribute with agrovoc uri'},
                {'id': 'CC-CCC-789789-CC789',
                 'message': 'openag:tag element must have @vocabulary attribute',
                 'path': '/iati-activities/iati-activity[3]/openag:tag',
                 'rule': 'element must have @vocabulary attribute with code for "maintained by the reporting organisation"'},
                {'id': 'DD-DDD-789789-DD789',
                 'message': 'the activity should include at least one openag:tag element',
                 'path': '/iati-activities/iati-activity[4]',
                 'rule': 'element is expected'}]

    file_path = os.path.join('cove_iati', 'fixtures', 'iati_openag_tag.xml')
    output_dir = os.path.join('media', str(uuid.uuid4()))
    call_command('iati_cli', file_path, output_dir=output_dir, openag=True)

    with open(os.path.join(output_dir, 'results.json')) as fp:
        results = json.load(fp)

    ruleset_errors = results.get('ruleset_errors_openag')
    ruleset_errors.sort(key=lambda i: i['path'])

    zipped_results = zip(expected, ruleset_errors)

    for expected, actual in zipped_results:
        assert expected['id'] == actual['id']
        assert expected['message'] == actual['message']
        assert expected['path'] == actual['path']
        assert expected['rule'] == actual['rule']
