import json
import os
import re

from bdd_tester import bdd_tester


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
    bdd_tester(etree=lxml_etree, features=['cove_iati/rulesets/iati_standard_ruleset/'], output_path=output_dir)
    ruleset_errors = []

    for output_file in os.listdir(output_dir):
        with open(os.path.join(output_dir, output_file)) as fp:
            scenario_outline = re.sub(r':', '/', output_file[:-7]).split('_')
            for line in fp:
                line = line.strip()

                if line:
                    json_line = json.loads(line)
                    message = json_line['message']
                    activity_id = json_line['id']
                    if message.startswith('and') or message.startswith('or'):
                        ruleset_errors[-1]['explanation'] += ' {}'.format(message)
                        continue
                    rule_error = {
                        'path': scenario_outline[0],
                        'rule': ' '.join(scenario_outline[1:]),
                        'message': message,
                        'id': activity_id
                    }
                    ruleset_errors.append(rule_error)

    return ruleset_errors
