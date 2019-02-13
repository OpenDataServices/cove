import os
import glob
from functools import lru_cache
from collections import defaultdict
import json

from lxml import etree as ET
from lxml.etree import Element


def process_mapping(schema_directory):
    mappings = ET.parse(os.path.join(schema_directory, 'mapping.xml'))
    all_mappings = {}
    for mapping in mappings.getroot().xpath('//mapping'):
        codelist = mapping.find('codelist').attrib['ref']
        all_mappings[codelist] = {"path": mapping.find('path').text}
        if mapping.find('condition') is not None:
            all_mappings[codelist]['condition'] = mapping.find('condition').text
    return all_mappings


def parse_codelist(filename):
    codelist = ET.parse(filename)
    codelist_root = codelist.getroot()
    metadata = codelist_root.find('metadata')

    codelist_data = {}

    codelist_data['name'] = metadata.find('name').find('narrative').text
    description = metadata.find('description')
    if description is not None:
        codelist_data['description'] = description.find('narrative').text

    codelist_values = {}
    for codelist_item in codelist_root.xpath('//codelist-item'):
        codelist_values[codelist_item.find('code').text] = {
            "name": codelist_item.find('name').find('narrative').text,
            "description": codelist_item.find('description').find('narrative').text,
        }

    codelist_data['values'] = codelist_values
    return codelist_data


@lru_cache()
def embedded_codelists(schema_directory):
    mappings = process_mapping(schema_directory)
    embedded_codelists = {}
    for filename in glob.glob(os.path.join(schema_directory, 'codelists') + '/' + '*.xml'):
        codelist_name = filename.split('/')[-1].split('.')[0]
        if codelist_name not in mappings:
            continue
        embedded_codelists[codelist_name] = mappings[codelist_name]
        embedded_codelists[codelist_name].update(parse_codelist(filename))
        embedded_codelists[codelist_name]["filename"] = codelist_name

    return embedded_codelists


def create_path_to_codelists(codelists):
    path_to_codelist = {}
    for name, codelist in codelists.items():
        # remove '//' from start of xpaths as we are going to compare
        # paths to the end
        reduced_path = codelist['path'].lstrip('/')
        path_to_codelist[reduced_path] = codelist
    return path_to_codelist


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
    path_to_codelist = create_path_to_codelists(codelist_values)

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
        for codelist_path, codelist_obj in path_to_codelist.items():
            # all codelists start with //
            if non_number_path.endswith(codelist_path):
                codelist_data = codelist_obj
                break

        #codelist = path_to_codelist.get(non_number_path)
        if not codelist_data:
            continue

        if str(value) in codelist_data['values']:
            continue

        invalid_codelist_value = {
            "path": path,
            "xpath": parsed.getpath(element) + '/' + attr_name,
            "value": value,
            "current_identifier": current_identifier,
            "codelist_name": codelist_data['name'],
            "filename": codelist_data['filename'],
            "codelist_path": codelist_data['path'],
        }

        if source_map:
            non_zero_path = path.replace('/0/', '/')
            invalid_codelist_value['source_map_data'] = source_map_data[non_zero_path][0]

        invalid_codelist_values.append(invalid_codelist_value)

    return invalid_codelist_values


def invalid_embedded_codelist_values(schema_directory, filename, source_map=None):
    return invalid_codelist_values(embedded_codelists(schema_directory), filename, source_map)


def aggregate_results(codelist_values):
    codelist_aggregate = defaultdict(list)

    for codelist_value in codelist_values:
        codelist_aggregate[codelist_value['codelist_path']].append(codelist_value)

    codelist_aggregate_list = []

    for invalid_list in codelist_aggregate.values():
        codelist_aggregate_list.append({
            "invalid_list": invalid_list,
            "filename": invalid_list[0]["filename"],
            "codelist_name": invalid_list[0]["codelist_name"],
            "codelist_path": invalid_list[0]["codelist_path"],
            "codelist_path_slug": invalid_list[0]["codelist_path"].lstrip('/').replace('/', '-').replace('@', '-')
        })

    return codelist_aggregate_list
