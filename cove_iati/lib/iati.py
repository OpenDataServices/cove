import json
import os
import re

import defusedxml.lxml as etree
import lxml.etree
from bdd_tester import bdd_tester
from django.utils.translation import ugettext_lazy as _

from .schema import SchemaIATI
from cove.lib.exceptions import CoveInputDataError, UnrecognisedFileTypeXML
from cove.lib.tools import ignore_errors


def common_checks_context_iati(context, upload_dir, data_file, file_type, api=False, openag=False, orgids=False):
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
        except UnicodeDecodeError as err:
            raise CoveInputDataError(context={
                'sub_title': _("Sorry we can't process that data"),
                'link': 'index',
                'link_text': _('Try Again'),
                'msg': _('We think you tried to upload a XML file, but the encoding is incorrect.'
                         '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                         '</span> <strong>Error message:</strong> {}'.format(err)),
                'error': format(err)
            })
        schema_tree = etree.parse(schema_fp)

    schema = lxml.etree.XMLSchema(schema_tree)
    schema.validate(tree)
    lxml_errors = lxml_errors_generator(schema.error_log)
    errors_all = format_lxml_errors(lxml_errors)
    invalid_data = bool(schema.error_log)
    return_on_error = [{'message': 'There was a problem running ruleset checks',
                        'exception': True}]

    # Validation errors
    if file_type != 'xml':
        with open(os.path.join(upload_dir, 'cell_source_map.json')) as cell_source_map_fp:
            cell_source_map = json.load(cell_source_map_fp)
    if os.path.exists(validation_errors_path):
        with open(validation_errors_path) as validation_error_fp:
            validation_errors = json.load(validation_error_fp)
    else:
        validation_errors = get_xml_validation_errors(errors_all, file_type, cell_source_map)
        if not api:
            with open(validation_errors_path, 'w+') as validation_error_fp:
                validation_error_fp.write(json.dumps(validation_errors))

    # Ruleset errors
    ruleset_errors = get_iati_ruleset_errors(
        tree,
        os.path.join(upload_dir, 'ruleset'),
        api=api,
        ignore_errors=invalid_data,
        return_on_error=return_on_error
    )

    if openag:
        ruleset_errors_ag = get_openag_ruleset_errors(
            tree,
            os.path.join(upload_dir, 'ruleset_openang'),
            ignore_errors=invalid_data,
            return_on_error=return_on_error
        )
        context.update({'ruleset_errors_openag': ruleset_errors_ag})
    if orgids:
        ruleset_errors_orgids = get_orgids_ruleset_errors(
            tree,
            os.path.join(upload_dir, 'ruleset_orgids'),
            ignore_errors=invalid_data,
            return_on_error=return_on_error
        )
        context.update({'ruleset_errors_orgids': ruleset_errors_orgids})

    context.update({
        'validation_errors': sorted(validation_errors.items()),
        'ruleset_errors': ruleset_errors
    })

    if not api:
        context.update({
            'validation_errors_count': sum(len(value) for value in validation_errors.values()),
            'cell_source_map': cell_source_map,
            'first_render': False
        })
        if ruleset_errors:
            ruleset_errors_by_activity = get_iati_ruleset_errors(
                tree,
                os.path.join(upload_dir, 'ruleset'),
                group_by='activity',
                ignore_errors=invalid_data,
                return_on_error=return_on_error
            )
            context['ruleset_errors'] = [ruleset_errors, ruleset_errors_by_activity]
        count_ruleset_errors = 0
        for rules in ruleset_errors.values():
            for errors in rules.values():
                count_ruleset_errors += len(errors)
        context['ruleset_errors_count'] = count_ruleset_errors

    return context


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

        if 'element is not expected' in message or 'Missing child element' in message:
            message = message.replace('. Expected is (', ', expected is').replace(' )', '')
        elif 'required but missing' in message or 'content other than whitespace is not allowed' in message:
            pass
        else:
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
            validation_errors[validation_key].append({'path': error['path'], 'value': error['value']})

    return validation_errors


def format_ruleset_errors(output_dir):
    ruleset_errors = []

    for output_file in os.listdir(output_dir):
        with open(os.path.join(output_dir, output_file)) as fp:
            scenario_outline = ' '.join(re.sub('\.', '/', output_file[:-7]).split('_'))
            for line in fp:
                line = line.strip()

                if line:
                    json_line = json.loads(line)
                    for error in json_line['errors']:
                        rule_error = {
                            'id': json_line['id'],
                            'path': error['path'],
                            'rule': scenario_outline,
                            'explanation': error['explanation'],
                            'ruleset': json_line['ruleset']
                        }
                        ruleset_errors.append(rule_error)

    return ruleset_errors


def _ruleset_errors_by_rule(flat_errors):
    ruleset_errors = {}
    for error in flat_errors:
        if error['ruleset'] not in ruleset_errors:
            ruleset_errors[error['ruleset']] = {}
        if error['rule'] not in ruleset_errors[error['ruleset']]:
            ruleset_errors[error['ruleset']][error['rule']] = []
        ruleset_errors[error['ruleset']][error['rule']].append([
            error['id'], error['explanation'], error['path']
        ])
    return ruleset_errors


def _ruleset_errors_by_activity(flat_errors):
    ruleset_errors = {}
    for error in flat_errors:
        if error['id'] not in ruleset_errors:
            ruleset_errors[error['id']] = {}
        if error['ruleset'] not in ruleset_errors[error['id']]:
            ruleset_errors[error['id']][error['ruleset']] = []
        ruleset_errors[error['id']][error['ruleset']].append([
            error['rule'], error['explanation'], error['path']
        ])
    return ruleset_errors


@ignore_errors
def get_iati_ruleset_errors(lxml_etree, output_dir, group_by='rule', api=False):
    if group_by not in ['rule', 'activity']:
        raise ValueError('Only `rule` or `activity` are valid values for group_by argument')

    bdd_tester(etree=lxml_etree, features=['cove_iati/rulesets/iati_standard_v2_ruleset/'],
               output_path=output_dir)

    if not os.path.isdir(output_dir):
        return []
    if api:
        return format_ruleset_errors(output_dir)
    if group_by == 'rule':
        return _ruleset_errors_by_rule(format_ruleset_errors(output_dir))
    else:
        return _ruleset_errors_by_activity(format_ruleset_errors(output_dir))


@ignore_errors
def get_openag_ruleset_errors(lxml_etree, output_dir):
    bdd_tester(etree=lxml_etree, features=['cove_iati/rulesets/iati_openag_ruleset/'],
               output_path=output_dir)

    if not os.path.isdir(output_dir):
        return []
    return format_ruleset_errors(output_dir)


@ignore_errors
def get_orgids_ruleset_errors(lxml_etree, output_dir):
    bdd_tester(etree=lxml_etree, features=['cove_iati/rulesets/iati_orgids_ruleset/'],
               output_path=output_dir)

    if not os.path.isdir(output_dir):
        return []
    return format_ruleset_errors(output_dir)


def get_file_type(file):
    if isinstance(file, str):
        name = file.lower()
    else:
        name = file.name.lower()
    if name.endswith('.xml'):
        return 'xml'
    elif name.endswith('.xlsx'):
        return 'xlsx'
    elif name.endswith('.csv'):
        return 'csv'
    else:
        raise UnrecognisedFileTypeXML
