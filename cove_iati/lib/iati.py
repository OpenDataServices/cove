import json
import re


def lxml_errors_generator(schema_error_log):
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

        val_start = error['message'].find(": '")
        value = error['message'][val_start + len(": '"):]
        val_end = value.find("'")
        value = value[:val_end]
        message = error['message'].replace('Element ', '').replace(": '{}'".format(value), '')

        yield {'path': path, 'message': message, 'value': value}


def get_xml_validation_errors(errors, file_type, cell_source_map):
    validation_errors = {}
    for error in errors:
        validation_key = json.dumps(['', error['message']])
        if not validation_errors.get(validation_key):
            validation_errors[validation_key] = []

        if file_type != 'xml':
            cell_source_map_paths = cell_source_map.keys()
            generic_error_path = re.sub(r'/\d+', '', error['path'])
            for cell_path in cell_source_map_paths:
                if len(validation_errors[validation_key]) == 3:
                    break
                generic_cell_path = re.sub(r'/\d+', '', cell_path)
                if generic_error_path == generic_cell_path:
                    if len(cell_source_map[cell_path][0]) > 2:
                        sources = {
                            'sheet': cell_source_map[cell_path][0][0],
                            "col_alpha": cell_source_map[cell_path][0][1],
                            'row_number': cell_source_map[cell_path][0][2],
                            'header': cell_source_map[cell_path][0][3],
                            'path': cell_path,
                            'value': error['value']
                        }
                        validation_errors[validation_key].append(sources)
        else:
            validation_errors[validation_key].append({'path': error['path']})

    return validation_errors
