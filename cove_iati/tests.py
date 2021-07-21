import pytest
import defusedxml.lxml as etree
import json
import lxml.etree
import os
import uuid
import tempfile

from django.core.management import call_command

from .lib import iati
from .lib import api
from .lib.process_codelists import invalid_embedded_codelist_values
from .lib.exceptions import RuleSetStepException
from .rulesets.utils import invalid_date_format, get_child_full_xpath, get_xobjects, register_ruleset_errors


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
    <iati-activity>
      <element id='element1'/>
      <element id='element2'/>
  </iati-activity>
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


@pytest.mark.parametrize(('date_string', 'boolean'), [
    ('2000-01-01', False),
    ('01-01-2000', True),
    ('2000/01/01', True)
])
def test_invalid_date_format(date_string, boolean):
    assert invalid_date_format(date_string) is boolean


def test_get_xobjects():
    activities_xml = etree.XML(XML_NS)
    activity_xml = activities_xml.getchildren()[0]
    xobjects = get_xobjects(activity_xml, 'element')
    assert xobjects[0].attrib.get('id') == 'element1'
    assert xobjects[1].attrib.get('id') == 'element2'


def test_get_full_xpath():
    expected_full_xpath = '/iati-activities/iati-activity/element[1]'
    activities_xml = etree.XML(XML_NS)
    activity_xml = activities_xml.getchildren()[0]
    element_xml = activity_xml.getchildren()[0]
    assert get_child_full_xpath(activity_xml, element_xml) == expected_full_xpath


def test_register_ruleset_errors_decorator():
    def decorated_func_errors(context):
        return context, ['errors']

    def decorated_func_no_errors(context):
        return context, []

    class Feature():
        name = 'feature name'

    class Context():
        xml = etree.XML(XML_NS).getchildren()[0]
        feature = Feature()

    context = Context()

    decorator_ns = register_ruleset_errors(['namespace'])
    decorated_func_errors = decorator_ns(decorated_func_errors)
    decorated_func_no_errors = decorator_ns(decorated_func_no_errors)

    decorator_no_ns = register_ruleset_errors(['undefined_ns'])
    decorated_func_no_ns = decorator_no_ns(decorated_func_no_errors)
    errors_ns = [{
        'explanation': 'rule not applied: the data does not define "undefined_ns" namespace '
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
    ('basic_iati_unordered_valid.csv', False, {}, [
        'basic_iati_unordered_valid.csv',
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
                       'value': ''},
                      {'description': "'recipient-country', attribute 'percentage' is not a valid value of the atomic type 'xs:decimal'.",
                       'path': "iati-activity/4/recipient-country/@percentage",
                       'value': 'bad number'}]

    exp_rulesets = [{'id': 'TZ-BRLA-1-AAA-123123-AA123',
                     'explanation': '2200-01-01 must be on or before today (2017-10-04)',
                     'path': '/iati-activities/iati-activity[1]/transaction[2]/transaction-date/@iso-date',
                     'rule': 'transaction/transaction-date/@iso-date date must be today or in the past'},
                   {'id': 'TZ-BRLA-3-BBB-123123-BB123',
                    'explanation': '2200-01-01 must be on or before today (2017-10-04)',
                    'path': '/iati-activities/iati-activity[2]/activity-date/@iso-date',
                    'rule': "activity-date[@type='2']/@iso-date must be today or in the past"},
                   {'id': 'TZ-BRLA-3-BBB-123123-BB123',
                    'explanation': '2200-01-01 must be on or before today (2017-10-04)',
                    'path': '/iati-activities/iati-activity[2]/transaction[2]/value/@value-date',
                    'rule': 'transaction/value/@value-date must be today or in the past'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'explanation': 'Neither @ref nor narrative/text() have been found',
                    'path': '/iati-activities/iati-activity[3]',
                    'rule': 'participating-org/@ref attribute or participating-org/narrative must be present'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'explanation': 'Start date (2010-01-01) must be before end date (2009-01-01)',
                    'path': '/iati-activities/iati-activity[3]/budget/period-start/@iso-date & '
                            '/iati-activities/iati-activity[3]/budget/period-end/@iso-date',
                    'rule': 'budget-period/period-start/@iso-date must be before budget-period/period-end/@iso-date'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'explanation': 'Text does not match the regex ?TZ-BRLA-5-CCC-123123-CC123',
                    'path': '/iati-activities/iati-activity[3]/iati-identifier/text()',
                    'rule': 'identifier/text() should match the regex [^\\:\\&\\|\\?]+'},
                   #{'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    #'explanation': '?TZ-BRLA-5 does not match the regex ^[^\\/\\&\\|\\?]+$',
                    #'path': '/iati-activities/iati-activity[3]/reporting-org/@ref',
                    #'rule': 'reporting-org/@ref should match the regex [^\\:\\&\\|\\?]+'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'explanation': 'Either sector or transaction/sector are expected (not both)',
                    'path': '/iati-activities/iati-activity[3]/sector & /iati-activities/iati-activity[3]'
                            '/transaction[1]/sector',
                    'rule': 'either sector or transaction/sector must be present'},
                   {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                    'explanation': 'Either sector or transaction/sector are expected (not both)',
                    'path': '/iati-activities/iati-activity[3]/sector & /iati-activities/iati-activity[3]'
                            '/transaction[2]/sector',
                    'rule': 'either sector or transaction/sector must be present'},
                   {'id': 'TZ-BRLA-5-DDD-123123-DD123',
                    'explanation': 'Neither activity-date[@type="1"] nor activity-date[@type="2"] have been found',
                    'path': '/iati-activities/iati-activity[4]',
                    'rule': 'activity-date[date @type="1"] or activity-date[@type="2"] must be present'},
                   {'id': 'TZ-BRLA-5-DDD-123123-DD123',
                    'explanation': '2400-01-01 must be on or before today (2017-10-04)',
                    'path': '/iati-activities/iati-activity[4]/activity-date/@iso-date',
                    'rule': "activity-date[@type='4']/@iso-date must be today or in the past"},
                   {
                    'id': 'TZ-BRLA-5-DDD-123123-DD123',
                    'explanation': 'recipient-country|recipient-region/@percentage adds up to 30%',
                    'path': '/iati-activities/iati-activity[4]/recipient-country',
                    'rule': 'recipient-country/@percentage and recipient-region/@percentage must sum to 100%'},
                   {'id': 'TZ-BRLA-9-EEE-123123-EE123',
                    'explanation': 'Neither activity-date[@type="1"] nor activity-date[@type="2"] have been found',
                    'path': '/iati-activities/iati-activity[5]',
                    'rule': 'activity-date[date @type="1"] or activity-date[@type="2"] must be present'},
                   {'id': 'TZ-BRLA-9-EEE-123123-EE123',
                    'explanation': 'recipient-country|recipient-region/@percentage adds up to 0%',
                    'path': '/iati-activities/iati-activity[5]/recipient-country',
                    'rule': 'recipient-country/@percentage and recipient-region/@percentage must sum to 100%'},
                    ]

    exp_org_rulesets = [
       {'id': '?TZ-BRLA-5-CCC-123123-CC123',
        'explanation': '?TZ-BRLA-5 does not match the regex ^[^\\/\\&\\|\\?]+$',
        'path': '/iati-activities/iati-activity[3]/reporting-org/@ref',
        'rule': 'reporting-org/@ref should match the regex [^\\:\\&\\|\\?]+'},
       {'id': 'TZ-BRLA-5-DDD-123123-DD123',
        'explanation': '?TZ-BRLA-8 does not match the regex ^[^\\/\\&\\|\\?]+$',
        'path': '/iati-activities/iati-activity[4]/participating-org/@ref',
        'rule': 'participating-org/@ref should match the regex [^\\:\\&\\|\\?]+'},
       {'id': 'TZ-BRLA-9-EEE-123123-EE123',
        'explanation': '?TZ-BRLA-101 does not match the regex ^[^\\/\\&\\|\\?]+$',
        'path': '/iati-activities/iati-activity[5]/transaction[1]/provider-org/@ref',
        'rule': 'transaction/provider-organisation/@ref should match the regex [^\\:\\&\\|\\?]+'},
       {'id': 'TZ-BRLA-9-EEE-123123-EE123',
        'explanation': '?TZ-BRLA-102 does not match the regex ^[^\\/\\&\\|\\?]+$',
        'path': '/iati-activities/iati-activity[5]/transaction[2]/receiver-org/@ref',
        'rule': 'transaction/receiver-organisation/@ref should match the regex [^\\:\\&\\|\\?]+'}
    ]

    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_ruleset_errors.xml')
    output_dir = os.path.join('media', str(uuid.uuid4()))
    call_command('iati_cli', file_path, output_dir=output_dir)

    with open(os.path.join(output_dir, 'results.json')) as fp:
        results = json.load(fp)

    assert not results.get('ruleset_errors_openag')
    assert not results.get('ruleset_errors_orgids')

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
        if 'on or before today' in expected['explanation']:
            assert expected['explanation'][:-13] == actual['explanation'][:-13]
        else:
            assert expected['explanation'] == actual['explanation']

    org_ruleset_errors = results.get('org_ruleset_errors')
    org_ruleset_errors.sort(key=lambda i: i['path'])
    zipped_org_ruleset_results = zip(exp_org_rulesets, org_ruleset_errors)

    for expected, actual in zipped_org_ruleset_results:
        assert expected['id'] == actual['id']
        assert expected['path'] == actual['path']
        assert expected['rule'] == actual['rule']


def test_cove_iati_cli_orgids_output():
    expected = [{'id': '?TZ-BRLA-5-CCC-123123-CC123',
                 'explanation': '@ref  does not start with a recognised org-ids prefix',
                 'path': '/iati-activities/iati-activity[3]/participating-org/@ref',
                 'rule': 'participating-org/@ref must have an org-ids prefix'},
                {'id': '?TZ-BRLA-5-CCC-123123-CC123',
                 'explanation': '@ref ?TZ-BRLA-5 does not start with a recognised org-ids prefix',
                 'path': '/iati-activities/iati-activity[3]/reporting-org/@ref',
                 'rule': 'reporting-org/@ref must have an org-ids prefix'},
                {'id': 'TZ-BRLA-5-DDD-123123-DD123',
                 'explanation': '@ref ?TZ-BRLA-8 does not start with a recognised org-ids prefix',
                 'path': '/iati-activities/iati-activity[4]/participating-org/@ref',
                 'rule': 'participating-org/@ref must have an org-ids prefix'},
                {'id': 'TZ-BRLA-9-EEE-123123-EE123',
                 'explanation': '@ref ?TZ-BRLA-101 does not start with a recognised org-ids prefix',
                 'path': '/iati-activities/iati-activity[5]/transaction[1]/provider-org/@ref',
                 'rule': 'transaction/provider-org/@ref must have an org-ids prefix'},
                {'id': 'TZ-BRLA-9-EEE-123123-EE123',
                 'explanation': '@ref ?TZ-BRLA-102 does not start with a recognised org-ids prefix',
                 'path': '/iati-activities/iati-activity[5]/transaction[2]/receiver-org/@ref',
                 'rule': 'transaction/receiver-org/@ref must have an org-ids prefix'}]

    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_ruleset_errors.xml')
    output_dir = os.path.join('media', str(uuid.uuid4()))
    call_command('iati_cli', file_path, output_dir=output_dir, orgids=True)

    with open(os.path.join(output_dir, 'results.json')) as fp:
        results = json.load(fp)

    assert not results.get('ruleset_errors_openag')

    ruleset_errors = results.get('ruleset_errors_orgids')
    ruleset_errors.sort(key=lambda i: i['path'])
    zipped_results = zip(expected, ruleset_errors)

    for expected, actual in zipped_results:
        assert expected['id'] == actual['id']
        assert expected['explanation'] == actual['explanation']
        assert expected['path'] == actual['path']
        assert expected['rule'] == actual['rule']


def test_cove_iati_cli_openag_output():
    expected = [{'id': 'AA-AAA-123123-AA123',
                 'explanation': 'the activity should include at least one location element',
                 'path': '/iati-activities/iati-activity[1]',
                 'rule': 'location element must be present'},
                {'id': 'AA-AAA-123123-AA123',
                 'explanation': 'tag element must have @vocabulary attribute',
                 'path': '/iati-activities/iati-activity[1]/tag',
                 'rule': 'tag/@vocabulary must be present with a code for "maintained by the '
                         'reporting organisation"'},
                {'id': 'BB-BBB-123123-BB123',
                 'explanation': 'location/location-id element must have @code attribute',
                 'path': '/iati-activities/iati-activity[2]/location/location-id',
                 'rule': 'location/@code must be present'},
                {'id': 'BB-BBB-123123-BB123',
                 'explanation': '"http://bad.org" is not a valid value for @vocabulary-uri attribute (it '
                                'should be "http://aims.fao.org/aos/agrovoc/")',
                 'path': '/iati-activities/iati-activity[2]/tag/@vocabulary-uri',
                 'rule': 'tag/@vocabulary-uri must be present with an agrovoc uri'},
                {'id': 'CC-CCC-789789-CC789',
                 'explanation': 'location/location-id element must have @vocabulary attribute',
                 'path': '/iati-activities/iati-activity[3]/location/location-id',
                 'rule': 'location/@vocabulary must be present'},
                {'id': 'CC-CCC-789789-CC789',
                 'explanation': '"01" is not a valid value for @vocabulary attribute (it should be "1 or 98 or 99")',
                 'path': '/iati-activities/iati-activity[3]/tag/@vocabulary',
                 'rule': 'tag/@vocabulary must be present with a code for "maintained by the '
                         'reporting organisation"'},
                {'id': 'DD-DDD-789789-DD789',
                 'explanation': 'tag element must have @code attribute',
                 'path': '/iati-activities/iati-activity[4]/tag',
                 'rule': 'tag/@code must be present'},
                {'id': 'EE-DDD-789789-EE789',
                 'explanation': 'the activity should include at least one tag element',
                 'path': '/iati-activities/iati-activity[5]',
                 'rule': 'tag element must be present'},
                {'id': 'EE-DDD-789789-EE789',
                 'explanation': 'location must contain a location-id element',
                 'path': '/iati-activities/iati-activity[5]/location',
                 'rule': 'location/location-id must be present'}]

    file_path = os.path.join('cove_iati', 'fixtures', 'iati_openag_tag.xml')
    output_dir = os.path.join('media', str(uuid.uuid4()))
    call_command('iati_cli', file_path, output_dir=output_dir, openag=True)

    with open(os.path.join(output_dir, 'results.json')) as fp:
        results = json.load(fp)

    assert not results.get('ruleset_errors_orgids')

    ruleset_errors = results.get('ruleset_errors_openag')
    ruleset_errors.sort(key=lambda i: i.get('path'))
    zipped_results = zip(expected, ruleset_errors)

    for expected, actual in zipped_results:
        assert expected['id'] == actual['id']
        assert expected['explanation'] == actual['explanation']
        assert expected['path'] == actual['path']
        assert expected['rule'] == actual['rule']


def test_ruleset_error_exceptions_handling(validated_data):
    return_on_error = [{'message': 'There was a problem running ruleset checks', 'exception': True}]

    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_unordered_valid.xml')
    with open(file_path) as fp:
        valid_data_tree = etree.parse(fp)
    upload_dir = os.path.join('media', str(uuid.uuid4()))
    ruleset_errors = iati.get_iati_ruleset_errors(
        valid_data_tree,
        os.path.join(upload_dir, 'ruleset'),
        ignore_errors=False,
        return_on_error=return_on_error
    )
    assert ruleset_errors != return_on_error

    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_ruleset_errors.xml')
    with open(file_path) as fp:
        invalid_data_tree = etree.parse(fp)
    invalid_data_tree = etree.fromstring(INVALID_DATA)
    upload_dir = os.path.join('media', str(uuid.uuid4()))
    ruleset_errors = iati.get_iati_ruleset_errors(
        invalid_data_tree,  # Causes an exception in ruleset checks
        os.path.join(upload_dir, 'ruleset'),
        ignore_errors=True,  # Exception ignored
        return_on_error=return_on_error
    )
    assert ruleset_errors == return_on_error

    with pytest.raises(AttributeError):
        upload_dir = os.path.join('media', str(uuid.uuid4()))
        ruleset_errors = iati.get_iati_ruleset_errors(
            invalid_data_tree,  # Causes an exception in ruleset checks
            os.path.join(upload_dir, 'ruleset'),
            ignore_errors=False,  # Exception not ignored
            return_on_error=return_on_error
        )


def test_common_checks_context_iati_ruleset():
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_unordered_valid.xml')
    upload_dir = os.path.join('media', str(uuid.uuid4()))
    tree = iati.get_tree(file_path)
    context = iati.common_checks_context_iati({}, upload_dir, file_path, 'xml', tree, api=True)

    assert len(context['ruleset_errors']) == 3

    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_ruleset_errors.xml')
    upload_dir = os.path.join('media', str(uuid.uuid4()))
    tree = iati.get_tree(file_path)
    context = iati.common_checks_context_iati({}, upload_dir, file_path, 'xml', tree, api=True)

    assert len(context['ruleset_errors']) == 13
    assert len(context['org_ruleset_errors']) == 4


def test_common_checks_context_iati_org_validation():
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_org_valid.xml')
    upload_dir = os.path.join('media', str(uuid.uuid4()))
    tree = iati.get_tree(file_path)
    context = iati.common_checks_context_iati({}, upload_dir, file_path, 'xml', tree, api=True)
    assert len(context['validation_errors']) == 0


def test_post_api(client):
    file_path = os.path.join('cove_iati', 'fixtures', 'example.xml')
    resp = client.post('/api_test', {'file': open(file_path, 'rb'), 'name': 'example.xml'})

    assert resp.status_code == 200
    assert resp.json()['validation_errors'] == []
    assert resp.json()['file_type'] == 'xml'

    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_unordered_valid.xlsx')
    resp = client.post('/api_test', {'file': open(file_path, 'rb'), 'name': 'basic_iati_unordered_valid.xlsx'})

    assert resp.status_code == 200
    assert resp.json()['validation_errors'] == []
    assert resp.json()['file_type'] == 'xlsx'

    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_unordered_valid.xlsx')
    resp = client.post('/api_test', {'file': open(file_path, 'rb')})
    assert resp.status_code == 400
    assert resp.json() == {'name': ['This field is required.']}


def test_process_codelist():
    file_path = os.path.join('cove_iati', 'fixtures', 'unflattened_bad_codelist_xlsx.xml')
    source_map_path = os.path.join('cove_iati', 'fixtures', 'cell_source_map_bad_codelist_xlsx.json')
    schema_directory = os.path.join('cove_iati', 'iati_schemas', '2.03')
    result = invalid_embedded_codelist_values(schema_directory, file_path, source_map_path)
    assert len(result) == 3
    assert set(item['value'] for item in result) == set(["what", "is", "100"])


def test_embedded_codelist_full():
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_unordered_bad_codelist.xlsx')
    with tempfile.TemporaryDirectory() as tmpdirname:
        context = api.iati_json_output(tmpdirname, file_path)
        print('created temporary directory', tmpdirname)
    assert len(context['invalid_embedded_codelist_values']) == 3
    assert set(item['value'] for item in context['invalid_embedded_codelist_values']) == set(["what", "is", "100"])


def test_non_embedded_codelist_full():
    file_path = os.path.join('cove_iati', 'fixtures', 'example_codelist.xml')
    with tempfile.TemporaryDirectory() as tmpdirname:
        context = api.iati_json_output(tmpdirname, file_path)
        print('created temporary directory', tmpdirname)
    assert len(context['invalid_embedded_codelist_values']) == 1
    assert set(item['value'] for item in context['invalid_embedded_codelist_values']) == set(["100"])

    assert len(context['invalid_non_embedded_codelist_values']) == 3
    assert set(item['value'] for item in context['invalid_non_embedded_codelist_values']) == set(["616", "A2", "A3"])


def test_iati_identifier_count():
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_unordered_valid.xml')
    tree = iati.get_tree(file_path)

    assert iati.iati_identifier_count(tree) == 2


def test_iati_identifier_count_when_non_unique():
    file_path = os.path.join('cove_iati', 'fixtures', 'iati_openag_tag_repeat_identifiers.xml')
    tree = iati.get_tree(file_path)

    assert iati.iati_identifier_count(tree) == 5


def test_iati_identifier_count_when_none():
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_org_valid.xml')
    tree = iati.get_tree(file_path)

    assert iati.iati_identifier_count(tree) == 0


def test_organisation_identifier_count():
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_org_valid.xml')
    tree = iati.get_tree(file_path)

    assert iati.organisation_identifier_count(tree) == 1


def test_organisation_identifier_count_when_non_unique():
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_org_valid_repeat_identifiers.xml')
    tree = iati.get_tree(file_path)

    assert iati.organisation_identifier_count(tree) == 2


def test_organisation_identifier_count_when_none():
    file_path = os.path.join('cove_iati', 'fixtures', 'basic_iati_unordered_valid.xml')
    tree = iati.get_tree(file_path)

    assert iati.organisation_identifier_count(tree) == 0
