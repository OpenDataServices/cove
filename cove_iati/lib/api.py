import os
import json
import shutil

from .iati import common_checks_context_iati, get_file_type, get_tree
from .schema import SchemaIATI
from libcove.lib.converters import convert_spreadsheet
from libcove.config import LibCoveConfig
from cove_iati.settings import COVE_CONFIG


class APIException(Exception):
    pass


def context_api_transform(context):
    validation_errors = context.get('validation_errors')
    context['validation_errors'] = []

    if validation_errors:
        for error_group in validation_errors:
            error = json.loads(error_group[0])
            for path_value in error_group[1]:
                context['validation_errors'].append({
                    'description': error['message'],
                    'path': path_value.get('path', ''),
                    'value': path_value.get('value', '')
                })

    return context


def iati_json_output(output_dir, file, openag=False, orgids=False):
    context = {}
    file_type = get_file_type(file)
    context = {"file_type": file_type}
    file_type = context['file_type']

    lib_cove_config = LibCoveConfig()
    lib_cove_config.config.update(COVE_CONFIG)

    if file_type != 'xml':
        schema_iati = SchemaIATI()
        context.update(convert_spreadsheet(output_dir, '', file, file_type, lib_cove_config,
            cache=False, xml=True, xml_schemas=[
                schema_iati.activity_schema,
                schema_iati.organisation_schema,
                schema_iati.common_schema,
            ]))
        data_file = context['converted_path']
    else:
        data_file = file

    tree = get_tree(data_file)
    context = context_api_transform(
        common_checks_context_iati(context, output_dir, data_file, file_type, tree,
                                   api=True, openag=openag, orgids=orgids)
    )

    if file_type != 'xml':
        # Remove unwanted files in the output
        # TODO: can we do this by no writing the files in the first place?
        os.remove(os.path.join(output_dir, 'heading_source_map.json'))
        os.remove(os.path.join(output_dir, 'cell_source_map.json'))

        if file_type == 'csv':
            shutil.rmtree(os.path.join(output_dir, 'csv_dir'))

    ruleset_dirs = [os.path.join(output_dir, 'ruleset'),
                    os.path.join(output_dir, 'ruleset_org_regex'),
                    os.path.join(output_dir, 'ruleset_openag'),
                    os.path.join(output_dir, 'ruleset_orgids')]
    for directory in ruleset_dirs:
        if os.path.exists(directory):
            shutil.rmtree(directory)

    return context
