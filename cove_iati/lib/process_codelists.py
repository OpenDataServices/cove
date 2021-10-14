import os
import glob
from functools import lru_cache
from collections import defaultdict
import json

from lxml import etree as ET
from lxml.etree import Element
from django.conf import settings

dir_path = os.path.dirname(os.path.realpath(__file__))


def process_mapping(schema_directory):
    mappings = ET.parse(os.path.join(schema_directory, 'mapping.xml'))
    all_mappings = {}
    for mapping in mappings.getroot().xpath('//mapping'):
        codelist_name = mapping.find('codelist').attrib['ref']
        path = mapping.find('path').text
        all_mappings[path.lstrip('/')] = {
            "path": path,
            "codelist_name": codelist_name,
        }
        if mapping.find('condition') is not None:
            all_mappings[path.lstrip('/')]['condition'] = mapping.find('condition').text

    return all_mappings


def parse_codelist_filename(filename):
    return _parse_codelist_etree(ET.parse(filename).getroot())


def parse_codelist_content(content):
    return _parse_codelist_etree(ET.fromstring(content))


def _parse_codelist_etree(codelist_root):
    metadata = codelist_root.find('metadata')

    codelist_data = {}

    codelist_data['name'] = metadata.find('name').find('narrative').text
    description = metadata.find('description')
    if description is not None:
        codelist_data['description'] = description.find('narrative').text

    codelist_values = {}
    for codelist_item in codelist_root.xpath('//codelist-item'):
        description = ''
        description_tag = codelist_item.find('description')
        if description_tag:
            description = description_tag.find('narrative').text
        name = ''
        name_tag = codelist_item.find('name')
        if name_tag:
            name = name_tag.find('narrative').text
        codelist_values[codelist_item.find('code').text] = {
            "name": name,
            "description": description,
        }

    codelist_data['values'] = codelist_values
    return codelist_data


@lru_cache()
def embedded_codelists(schema_directory):
    mappings = process_mapping(schema_directory)
    embedded_codelists = {}
    for filename in glob.glob(os.path.join(schema_directory, 'codelists') + '/' + '*.xml'):
        codelist_name = filename.split('/')[-1].split('.')[0]
        for path, mapping in mappings.items():
            if codelist_name == mapping['codelist_name']:
                embedded_codelists[path] = mappings[path]
                embedded_codelists[path].update(parse_codelist_filename(filename))
                embedded_codelists[path]["filename"] = filename

    return embedded_codelists


@lru_cache()
def non_embedded_codelists(schema_directory):
    mappings = process_mapping(schema_directory)
    non_embedded_codelists = {}
    for path, mapping in mappings.items():
        if mapping['codelist_name'] in settings.NON_EMBEDDED_CODELISTS_URLS:
            url = settings.NON_EMBEDDED_CODELISTS_URLS[mapping['codelist_name']]
            request = settings.REQUESTS_SESSION_WITH_CACHING.get(url)
            request.raise_for_status()
            non_embedded_codelists[path] = mappings[path]
            non_embedded_codelists[path].update(parse_codelist_content(request.content))

    return non_embedded_codelists


def traverse_element(current_path, element, index, current_identifier=None):
    tag_name = None
    count = 0

    if element.tag == 'iati-activity':
        identfier_element = element.find('iati-identifier')
        if identfier_element is not None:
            current_identifier = identfier_element.text
    if element.tag == 'iati-organisation':
        identfier_element = element.find('organisation-identifier')
        if identfier_element is not None:
            current_identifier = element.find('organisation-identifier').text

    new_path = current_path + '/' + element.tag + '/' + str(index)
    for attr_name, value in element.attrib.items():
        yield new_path + '/@' + attr_name, element, attr_name, value, current_identifier

    for child in element.iterchildren(Element):
        if str(child.tag) == tag_name:
            count += 1
        else:
            count = 0
            tag_name = str(child.tag)
        yield from traverse_element(new_path, child, count, current_identifier)


def is_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def invalid_codelist_values(codelist_values, filename, source_map=None):

    parsed = ET.parse(filename)
    root = parsed.getroot()

    invalid_codelist_values = []

    if source_map:
        with open(source_map) as f:
            source_map_data = json.load(f)
        for key, value in list(source_map_data.items()):
            source_map_data[key.replace('/0/', '/')] = value

    for path, element, attr_name, value, current_identifier in traverse_element('', root, 0):
        if path.startswith('/iati-activities'):
            path = path[len('/iati-activities/0/'):]
        if path.startswith('/iati-organisations'):
            path = path[len('/iati-organisations/0/'):]

        non_number_path = '/'.join([item for item in path.split('/') if not is_int(item)])

        codelist_data = None
        codelist_selected_path = None
        for codelist_path, codelist_obj in codelist_values.items():
            # all codelists start with //
            if non_number_path.endswith(codelist_path):
                codelist_data = codelist_obj
                codelist_selected_path = codelist_path
                break

        if not codelist_data:
            continue

        if str(value) in codelist_data['values']:
            continue

        condition = codelist_data.get('condition')
        if condition:
            vocabulary = element.attrib.get('vocabulary')
            allow_empty_vocabulary = 'not(@vocabulary)' in condition
            if not vocabulary and not allow_empty_vocabulary:
                continue
            if vocabulary and vocabulary != '1':
                continue

        invalid_codelist_value = {
            "path": path,
            "xpath": parsed.getpath(element) + '/' + attr_name,
            "value": value,
            "current_identifier": current_identifier,
            "codelist_name": codelist_data['name'],
            "filename": codelist_data.get('filename'),
            "codelist_path": codelist_selected_path
        }

        if source_map:
            non_zero_path = path.replace('/0/', '/')
            invalid_codelist_value['source_map_data'] = source_map_data[non_zero_path][0]

        invalid_codelist_values.append(invalid_codelist_value)

    return invalid_codelist_values


def invalid_embedded_codelist_values(schema_directory, filename, source_map=None):
    return invalid_codelist_values(embedded_codelists(schema_directory), filename, source_map)


def invalid_non_embedded_codelist_values(schema_directory, filename, source_map=None):
    return invalid_codelist_values(non_embedded_codelists(schema_directory), filename, source_map)


def aggregate_results(codelist_values):
    codelist_aggregate = defaultdict(list)

    for codelist_value in codelist_values:
        codelist_aggregate[codelist_value['codelist_path']].append(codelist_value)

    codelist_aggregate_list = []

    for codelist_path, invalid_list in codelist_aggregate.items():
        codelist_aggregate_list.append({
            "invalid_list": invalid_list,
            "filename": invalid_list[0]["filename"],
            "codelist_name": invalid_list[0]["codelist_name"],
            "codelist_path": codelist_path,
            "codelist_path_slug": codelist_path.lstrip('/').replace('/', '-').replace('@', '-')
        })

    return codelist_aggregate_list
