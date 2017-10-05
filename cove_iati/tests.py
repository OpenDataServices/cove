import pytest
import defusedxml.lxml as etree
import json
import lxml.etree
import os
import uuid

from django.core.management import call_command

from .lib import iati
from cove_iati.lib.exceptions import RuleSetStepException
from cove_iati.rulesets.utils import register_ruleset_errors


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

XML_NS = '''
    <iati-activities xmlns:namespace="http://example.com">
      <element>element</element>
    </iati-activities>
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


def test_register_ruleset_errors_decorator():
    def decorated_func_errors(context):
        return context, ['errors']

    def decorated_func_no_errors(context):
        return context, []

    class Context():
        xml = etree.XML(XML_NS).getchildren()[0]
    context = Context()

    decorator_ns = register_ruleset_errors('namespace')
    decorated_func_errors = decorator_ns(decorated_func_errors)
    decorated_func_no_errors = decorator_ns(decorated_func_no_errors)

    decorator_no_ns = register_ruleset_errors('undefined_ns')
    decorated_func_no_ns = decorator_no_ns(decorated_func_no_errors)
    errors_ns = [{
        'message': 'rule not applied: the data does not define "undefined_ns" namespace '
                   '(@xmlns:undefined_ns)',
        'path': '/iati-activities/@xmlns'
    }]

    with pytest.raises(RuleSetStepException) as e:
        decorated_func_errors(context)
    assert e.value.args == (context, ['errors'])

    assert not decorated_func_no_errors(context)

    with pytest.raises(RuleSetStepException) as e:
        decorated_func_no_ns(context)
    assert e.value.args == (context, errors_ns)


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
def test_cove_iati_cli_dir_content(file_name, bad_xml, options, output):
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
    exp_rulesets = [{'id': 'TZ-BRLA-1-AAA-123123-AA123',
                     'message': '2200-01-01 must be on or before today (2017-10-04)',
                     'path': '/iati-activities/iati-activity[1]/transaction[2]/transaction-date/@iso-date',
                     'rule': 'transaction/transaction-date/@iso-date date must be today or in the past'},
                   {'id': 'TZ-BRLA-3-BBB-123123-BB123',
                    'message': '2200-01-01 must be on or before today (2017-10-04)',
                    'path': '/iati-activities/iati-activity[2]/activity-date/@iso-date',
                    'rule': "activity-date[@type='2']/@iso-date must be today or in the past"},
                   {'id': 'TZ-BRLA-3-BBB-123123-BB123',
                    'message': '2200-01-01 must be on or before today (2017-10-04)',
                    'path': '/iati-activities/iati-activity[2]/transaction[2]/value/@value-date',
                    'rule': 'transaction/value/@value-date must be today or in the past'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'message': 'Neither participating-org/@ref nor participating-org/narrative/text() '
                               'have been found',
                    'path': '/iati-activities/iati-activity[3]',
                    'rule': 'participating-org/@ref attribute or participating-org/narrative must be present'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'message': 'Start date (2010-01-01) must be before end date (2009-01-01)',
                    'path': '/iati-activities/iati-activity[3]/budget/period-start/@iso-date & '
                            '/iati-activities/iati-activity[3]/budget/period-end/@iso-date',
                    'rule': 'budget-period/period-start/@iso-date must be before budget-period/period-end/@iso-date'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'message': 'Text does not match the regex ?TZ-BRLA-5-CCC-123123-CC123',
                    'path': '/iati-activities/iati-activity[3]/iati-identifier/text()',
                    'rule': 'identifier/text() should match the regex [^\\:\\&\\|\\?]+'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'message': ' does not match the regex ^[^\\/\\&\\|\\?]+$',
                    'path': '/iati-activities/iati-activity[3]/participating-org/@ref',
                    'rule': 'participating-org/@ref/should match the regex [^\\:\\&\\|\\?]+'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'message': '?TZ-BRLA-5 does not match the regex ^[^\\/\\&\\|\\?]+$',
                    'path': '/iati-activities/iati-activity[3]/reporting-org/@ref',
                    'rule': 'reporting-org/@ref should match the regex [^\\:\\&\\|\\?]+'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'message': 'Either sector or transaction/sector are expected (not both)',
                    'path': '/iati-activities/iati-activity[3]/sector & /iati-activities/iati-activity[3]'
                            '/transaction[1]/sector',
                    'rule': 'either sector or transaction/sector must be present'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'message': 'Either sector or transaction/sector are expected (not both)',
                    'path': '/iati-activities/iati-activity[3]/sector & /iati-activities/iati-activity[3]'
                            '/transaction[2]/sector',
                    'rule': 'either sector or transaction/sector must be present'},
                   {'id': 'TZ-BRLA-5-DDD-123123-DD123',
                    'message': 'Neither activity-date[@type="1"] nor activity-date[@type="2"] have been found',
                    'path': '/iati-activities/iati-activity[4]',
                    'rule': 'activity-date[date @type="1"] or activity-date[@type="2"] must be present'},
                   {'id': 'TZ-BRLA-5-DDD-123123-DD123',
                    'message': '2400-01-01 must be on or before today (2017-10-04)',
                    'path': '/iati-activities/iati-activity[4]/activity-date/@iso-date',
                    'rule': "activity-date[@type='4']/@iso-date must be today or in the past"},
                   {'id': 'TZ-BRLA-5-DDD-123123-DD123',
                    'message': '?TZ-BRLA-8 does not match the regex ^[^\\/\\&\\|\\?]+$',
                    'path': '/iati-activities/iati-activity[4]/participating-org/@ref',
                    'rule': 'participating-org/@ref/should match the regex [^\\:\\&\\|\\?]+'},
                   {'id': 'TZ-BRLA-9-EEE-123123-EE123',
                    'message': 'Neither activity-date[@type="1"] nor activity-date[@type="2"] have been found',
                    'path': '/iati-activities/iati-activity[5]',
                    'rule': 'activity-date[date @type="1"] or activity-date[@type="2"] must be present'},
                   {'id': 'TZ-BRLA-9-EEE-123123-EE123',
                    'message': '?TZ-BRLA-101 does not match the regex ^[^\\/\\&\\|\\?]+$',
                    'path': '/iati-activities/iati-activity[5]/transaction[1]/provider-org/@ref',
                    'rule': 'transaction/provider-organisation/@ref should match the regex [^\\:\\&\\|\\?]+'},
                   {'id': 'TZ-BRLA-9-EEE-123123-EE123',
                    'message': '?TZ-BRLA-102 does not match the regex ^[^\\/\\&\\|\\?]+$',
                    'path': '/iati-activities/iati-activity[5]/transaction[2]/receiver-org/@ref',
                    'rule': 'transaction/receiver-organisation/@ref should match the regex [^\\:\\&\\|\\?]+'}]

    exp_validation = [{'description': "'activity-date', attribute 'iso-date' is not a valid value of "
                                      "the atomic type 'xs:date'.",
                       'path': 'iati-activity/0/activity-date/@iso-date',
                       'value': '22000101'},
                      {'description': "'budget': Missing child element(s), expected is value.",
                       'path': 'iati-activity/0/budget',
                       'value': ''},
                      {'description': "'transaction-date', attribute 'iso-date' is not a valid value "
                                      "of the atomic type 'xs:date'.",
                       'path': 'iati-activity/0/transaction/0/transaction-date/@iso-date',
                       'value': '22000101'},
                      {'description': "'budget': Missing child element(s), expected is value.",
                       'path': 'iati-activity/1/budget',
                       'value': ''},
                      {'description': "'period-end', attribute 'iso-date' is not a valid value of the "
                                      "atomic type 'xs:date'.",
                       'path': 'iati-activity/1/budget/period-end/@iso-date',
                       'value': '20140101'},
                      {'description': "'period-start', attribute 'iso-date' is not a valid value of "
                                      "the atomic type 'xs:date'.",
                       'path': 'iati-activity/1/budget/period-start/@iso-date',
                       'value': '20150101'},
                      {'description': "'value', attribute 'value-date' is not a valid value of the "
                                      "atomic type 'xs:date'.",
                       'path': 'iati-activity/1/transaction/0/value/@value-date',
                       'value': '24000101'},
                      {'description': "'activity-date', attribute 'iso-date' is not a valid value of "
                                      "the atomic type 'xs:date'.",
                       'path': 'iati-activity/2/activity-date/0/@iso-date',
                       'value': '22000101'},
                      {'description': "'activity-date', attribute 'iso-date' is not a valid value of "
                                      "the atomic type 'xs:date'.",
                       'path': 'iati-activity/2/activity-date/1/@iso-date',
                       'value': '24000101'},
                      {'description': "'budget': Missing child element(s), expected is value.",
                       'path': 'iati-activity/2/budget',
                       'value': ''},
                      {'description': "'participating-org': The attribute 'role' is required but missing.",
                       'path': "iati-activity/2/participating-org/@role' is required but missing",
                       'value': ''},
                      {'description': "'activity-date': The attribute 'type' is required but missing.",
                       'path': "iati-activity/4/activity-date/@type' is required but missing",
                       'value': ''}]

    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_ruleset_errors.xml')
    output_dir = os.path.join('media', str(uuid.uuid4()))
    call_command('iati_cli', file_path, output_dir=output_dir)

    with open(os.path.join(output_dir, 'results.json')) as fp:
        results = json.load(fp)

    assert not results.get('ruleset_errors_openag')

    validation_errors = results.get('validation_errors')
    validation_errors.sort(key=lambda i: i['path'])
    zipped_validation_results = zip(exp_validation, validation_errors)

    for expected, actual in zipped_validation_results:
        assert expected['description'] == actual['description']
        assert expected['path'] == actual['path']
        assert expected['value'] == actual['value']

    ruleset_errors = results.get('ruleset_errors')
    ruleset_errors.sort(key=lambda i: i['path'])
    zipped_ruleset_results = zip(exp_rulesets, ruleset_errors)

    for expected, actual in zipped_ruleset_results:
        assert expected['id'] == actual['id']
        assert expected['path'] == actual['path']
        assert expected['rule'] == actual['rule']
        if 'on or before today' in expected['message']:
            assert expected['message'][:-13] == actual['message'][:-13]
        else:
            assert expected['message'] == actual['message']


def test_cove_iati_cli_openag_output():
    expected = [{'id': 'AA-AAA-123123-AA123',
                 'message': 'the activity should include at least one location element',
                 'path': '/iati-activities/iati-activity[1]',
                 'rule': 'location element must be present'},
                {'id': 'AA-AAA-123123-AA123',
                 'message': 'openag:tag element must have @vocabulary attribute',
                 'path': '/iati-activities/iati-activity[1]/openag:tag',
                 'rule': 'openag:tag/@vocabulary must be present with a code for "maintained by the '
                         'reporting organisation"'},
                {'id': 'AA-AAA-123123-AA123',
                 'message': '@ref NO-ORGIDS-10000 does not start with a recognised org-ids prefix',
                 'path': '/iati-activities/iati-activity[1]/reporting-org/@ref',
                 'rule': 'reporting-org/@ref must have an org-ids prefix'},
                {'id': 'BB-BBB-123123-BB123',
                 'message': 'location/location-id element must have @code attribute',
                 'path': '/iati-activities/iati-activity[2]/location/location-id',
                 'rule': 'location/@code must be present'},
                {'id': 'BB-BBB-123123-BB123',
                 'message': '"http://bad.org" is not a valid value for @vocabulary-uri attribute (it '
                            'should be "http://aims.fao.org/aos/agrovoc/")',
                 'path': '/iati-activities/iati-activity[2]/openag:tag/@vocabulary-uri',
                 'rule': 'openag:tag/@vocabulary-uri must be present with an agrovoc uri'},
                {'id': 'BB-BBB-123123-BB123',
                 'message': '@ref NO-ORGIDS-40000 does not start with a recognised org-ids prefix',
                 'path': '/iati-activities/iati-activity[2]/participating-org/@ref',
                 'rule': 'participating-org/@ref must have an org-ids prefix'},
                {'id': 'CC-CCC-789789-CC789',
                 'message': 'location/location-id element must have @vocabulary attribute',
                 'path': '/iati-activities/iati-activity[3]/location/location-id',
                 'rule': 'location/@vocabulary must be present'},
                {'id': 'CC-CCC-789789-CC789',
                 'message': '"01" is not a valid value for @vocabulary attribute (it should be "98 or 99")',
                 'path': '/iati-activities/iati-activity[3]/openag:tag/@vocabulary',
                 'rule': 'openag:tag/@vocabulary must be present with a code for "maintained by the '
                         'reporting organisation"'},
                {'id': 'DD-DDD-789789-DD789',
                 'message': 'openag:tag element must have @code attribute',
                 'path': '/iati-activities/iati-activity[4]/openag:tag',
                 'rule': 'openag:tag/@code must be present'},
                {'id': 'EE-DDD-789789-EE789',
                 'message': 'the activity should include at least one openag:tag element',
                 'path': '/iati-activities/iati-activity[5]',
                 'rule': 'openag:tag element must be present'},
                {'id': 'EE-DDD-789789-EE789',
                 'message': 'location must contain a location-id element',
                 'path': '/iati-activities/iati-activity[5]/location',
                 'rule': 'location/location-id must be present'}]

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
