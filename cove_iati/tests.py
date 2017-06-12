import pytest
from lxml import etree

from .lib.iati import lxml_errors_generator, format_lxml_errors, get_xml_validation_errors


def test_lxml_errors_generator():
    schema_tree = etree.XML('''
       <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
         <xsd:element name="a" type="xsd:integer"/>
         <xsd:element name="b" type="xsd:integer"
       </xsd:schema>
    ''')
    schema = etree.XMLSchema(schema_tree)


def test_format_lxml_errors():
    pass


def test_get_xml_validation_errors():
    pass
