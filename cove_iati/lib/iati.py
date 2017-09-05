import json
import os
import re

from bdd_tester import bdd_tester
import defusedxml.lxml as etree
import lxml.etree
from django.utils.translation import ugettext_lazy as _

from .iati_utils import sort_iati_xml_file
from .schema import SchemaIATI
from cove.lib.api import context_api_transform
from cove.lib.converters import convert_spreadsheet
from cove.lib.exceptions import CoveInputDataError
from cove.lib.tools import get_file_type


def common_checks_context_iati(upload_dir, data_file, file_type):
    schema_aiti = SchemaIATI()
    lxml_errors = {}
    cell_source_map = {}
    validation_errors_path = os.path.join(upload_dir, 'validation_errors-2.json')

    with open(data_file) as fp, open(schema_aiti.activity_schema) as schema_fp:
        try:
            tree = etree.parse(fp)
        except lxml.etree.XMLSyntaxError as err:
            raise CoveInputDataError(context={
                'sub_title': _("Sorry we can't process that data"),
                'link': 'index',
                'link_text': _('Try Again'),
                'msg': _('We think you tried to upload a XML file, but it is not well formed XML.'
                         '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                         '</span> <strong>Error message:</strong> {}'.format(err)),
                'error': format(err)
            })
        schema_tree = etree.parse(schema_fp)
        schema = lxml.etree.XMLSchema(schema_tree)
        schema.validate(tree)
        lxml_errors = lxml_errors_generator(schema.error_log)
        ruleset_errors = get_ruleset_errors(tree, os.path.join(upload_dir, 'ruleset'))

    errors_all = format_lxml_errors(lxml_errors)

    if file_type != 'xml':
        with open(os.path.join(upload_dir, 'cell_source_map.json')) as cell_source_map_fp:
            cell_source_map = json.load(cell_source_map_fp)

    if os.path.exists(validation_errors_path):
        with open(validation_errors_path) as validation_error_fp:
            validation_errors = json.load(validation_error_fp)
    else:
        validation_errors = get_xml_validation_errors(errors_all, file_type, cell_source_map)

        with open(validation_errors_path, 'w+') as validation_error_fp:
            validation_error_fp.write(json.dumps(validation_errors))

    return {
        'validation_errors': sorted(validation_errors.items()),
        'validation_errors_count': sum(len(value) for value in validation_errors.values()),
        'ruleset_errors': ruleset_errors,
        'ruleset_errors_count': len(ruleset_errors),
        'cell_source_map': cell_source_map,
        'first_render': False
    }


def lxml_errors_generator(schema_error_log):
    '''Yield dict with lxml error path and message

    Be aware that lxml does not include path indexes for single item arrays.

    one activity in data:
        iati-activities/iati-activity/activity-date/@iso-date

    two activities in data:
        iati-activities/iati-activity[1]/activity-date/@iso-date
        iati-activities/iati-activity[2]/activity-date/@iso-date

    This causes a problem when matching lxml error paths and cell source paths
    as the latter does include an index position for sequences with a single array.
    '''
    for error in schema_error_log:
        yield {'path': error.path, 'message': error.message}


def format_lxml_errors(lxml_errors):
    '''Convert lxml validation errors into structured errors'''
    for error in lxml_errors:
        # lxml uses path indexes starting from 1 in square brackets
        indexes = ['/{}'.format(str(int(i[1:-1]) - 1)) for i in re.findall(r'\[\d+\]', error['path'])]

        attribute = None
        attr_start = error['message'].find('attribute')
        if attr_start != -1:
            attribute = error['message'][attr_start + len("attribute '"):]
            attr_end = attribute.find("':")
            attribute = attribute[:attr_end]

        path = re.sub(r'\[\d+\]', '{}', error['path']).format(*indexes)
        path = re.sub(r'/iati-activities/', '', path)
        if attribute:
            path = '{}/@{}'.format(path, attribute)
        
        message = error['message']
        value = ''
        if 'element is not expected' not in message:
            val_start = error['message'].find(": '")
            value = error['message'][val_start + len(": '"):]
            val_end = value.find("'")
            value = value[:val_end]
        message = message.replace('Element ', '').replace(": '{}'".format(value), '')

        yield {'path': path, 'message': message, 'value': value}


def get_zero_paths_list(cell_path):
    '''Get all combinations of zeroes removed/not removed in a cell source path

    Returns a list. The list doesn't include the original path.

    e.g:
        'path/0/to/1/cell/0/source' will produce:

        ['path/1/to/1/cell/0/source',
         'path/0/to/1/cell/1/source',
         'path/to/1/cell/source']
    '''
    cell_zero_indexes, cell_zero_combinations, zero_paths_list = [], [], []
    cell_path_chars = cell_path.split('/')

    for index, char in enumerate(cell_path_chars):
        if char == '0':
            cell_zero_indexes.append(index)

    n_zeros = len(cell_zero_indexes)
    for i in range(1, 2 ** n_zeros):
        cell_zero_combinations.append(bin(i)[2:].zfill(n_zeros))

    for bin_repr in cell_zero_combinations:
        for index_bit in zip(cell_zero_indexes, bin_repr):
            if index_bit[1] == '0':
                cell_path_chars[index_bit[0]] = '0'
            else:
                cell_path_chars[index_bit[0]] = None
        path = '/'.join(filter(bool, cell_path_chars))
        zero_paths_list.append(path)

    return zero_paths_list


def error_path_source(error, cell_source_paths, cell_source_map, missing_zeros=False):
    source = {}
    found_path = None

    if missing_zeros:
        for cell_path in cell_source_paths:
            if error['path'] in get_zero_paths_list(cell_path):
                found_path = cell_path
                break
    else:
        for cell_path in cell_source_paths:
            if cell_path == error['path']:
                found_path = cell_path
                break

    if found_path:
        if len(cell_source_map[cell_path][0]) > 2:
            source = {
                'sheet': cell_source_map[cell_path][0][0],
                "col_alpha": cell_source_map[cell_path][0][1],
                'row_number': cell_source_map[cell_path][0][2],
                'header': cell_source_map[cell_path][0][3],
                'path': cell_path,
                'value': error['value']
            }
        else:
            source = {
                'sheet': cell_source_map[cell_path][0][0],
                'row_number': cell_source_map[cell_path][0][1],
                'header': cell_path,
                'path': cell_path,
                'value': error['value']
            }
    return source


def get_xml_validation_errors(errors, file_type, cell_source_map):
    validation_errors = {}
    if file_type != 'xml':
        cell_source_map_paths = {}
        for cell_path in cell_source_map.keys():
            generic_cell_path = re.sub(r'/\d+', '', cell_path)
            if cell_source_map_paths.get(generic_cell_path):
                cell_source_map_paths[generic_cell_path].append(cell_path)
            else:
                cell_source_map_paths[generic_cell_path] = [cell_path]

    for error in errors:
        validation_key = json.dumps(['', error['message']])
        if not validation_errors.get(validation_key):
            validation_errors[validation_key] = []

        if file_type != 'xml':
            generic_error_path = re.sub(r'/\d+', '', error['path'])
            cell_paths = cell_source_map_paths.get(generic_error_path, [])
            source = error_path_source(error, cell_paths, cell_source_map)
            if source:
                validation_errors[validation_key].append(source)
            else:
                source = error_path_source(error, cell_paths, cell_source_map, missing_zeros=True)
                validation_errors[validation_key].append(source)
        else:
            validation_errors[validation_key].append({'path': error['path']})

    return validation_errors


def get_ruleset_errors(lxml_etree, output_dir):
    bdd_tester(etree=lxml_etree, features=['cove_iati/rulesets/iati_standard_v2_ruleset/'],
               output_path=output_dir)
    ruleset_errors = []

    if not os.path.isdir(output_dir):
        return ruleset_errors

    for output_file in os.listdir(output_dir):
        with open(os.path.join(output_dir, output_file)) as fp:
            scenario_outline = re.sub(r':', '/', output_file[:-7]).split('_')
            for line in fp:
                line = line.strip()

                if line:
                    json_line = json.loads(line)
                    for error in json_line['errors']:
                        message = error['message']
                        activity_id = json_line['id']
                        if message.startswith('and') or message.startswith('or'):
                            ruleset_errors[-1]['message'] += ' {}'.format(message)
                            continue
                        rule_error = {
                            'path': error['path'] or scenario_outline[0],
                            'rule': ' '.join(scenario_outline[1:]),
                            'message': message,
                            'id': activity_id
                        }
                        ruleset_errors.append(rule_error)

    return ruleset_errors


def cli_json_output(output_dir, file):
    context = {}
    file_type = get_file_type(file)
    context = {"file_type": file_type}
    file_type = context['file_type']

    if file_type != 'xml':
        schema_iati = SchemaIATI()
        context.update(convert_spreadsheet(output_dir, '', file, file_type,
                       schema_iati.activity_schema, xml=True, cache=False))
        data_file = context['converted_path']
        # sort converted xml
        sort_iati_xml_file(context['converted_path'], context['converted_path'])
    else:
        data_file = file

    # context = context_api_transform(
    #     context.update(common_checks_context_iati(output_dir, data_file, file_type))
    # )

    context.update(common_checks_context_iati(output_dir, data_file, file_type))

    return context
