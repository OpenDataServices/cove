import pytest
import defusedxml.lxml as etree

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
        schema_tree = etree.XMLSchema(schema_xml)
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
