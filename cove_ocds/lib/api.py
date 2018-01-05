import json
import os
import re

from .schema import SchemaOCDS
from .ocds import common_checks_ocds
from cove.lib.common import get_spreadsheet_meta_data
from cove.lib.converters import convert_spreadsheet, convert_json
from cove.lib.tools import get_file_type


class APIException(Exception):
    pass


def context_api_transform(context):
    validation_errors = context.get('validation_errors')
    context['validation_errors'] = []

    context.pop('validation_errors_count')

    extensions = context.get('extensions')
    context['extensions'] = {}

    deprecated_fields = context.get('deprecated_fields')
    context['deprecated_fields'] = []

    additional_fields = context.pop('data_only')
    context['additional_fields'] = []
    context.pop('additional_fields_count')

    if validation_errors:
        for error_group in validation_errors:
            error_type, error_description, error_field = [
                re.sub('(\[?|\s?)\"\]?', '', err) for err in error_group[0].split(',')
            ]
            for path_value in error_group[1]:
                context['validation_errors'].append({
                    'type': error_type,
                    'field': error_field,
                    'description': error_description,
                    'path': path_value.get('path', ''),
                    'value': path_value.get('value', '')
                })

    if extensions:
        invalid_extensions = extensions.get('invalid_extension')
        context['extensions']['extensions'] = []
        for key, value in extensions['extensions'].items():
            if key not in invalid_extensions:
                context['extensions']['extensions'].append(value)
        context['extensions']['invalid_extensions'] = []
        for key, value in invalid_extensions.items():
            context['extensions']['invalid_extensions'].append([key, value])
        context['extensions']['extended_schema_url'] = extensions['extended_schema_url']
        context['extensions']['is_extended_schema'] = extensions['is_extended_schema']

    if deprecated_fields:
        for key, value in deprecated_fields.items():
            value.update({'field': key})
            context['deprecated_fields'].append(value)

    if additional_fields:
        for field_group in additional_fields:
            context['additional_fields'].append({
                'path': field_group[0],
                'field': field_group[1],
                'usage_count': field_group[2]
            })

    return context


def ocds_json_output(output_dir, file, schema_version, convert, cache_schema=False):
    context = {}
    file_type = get_file_type(file)
    context = {"file_type": file_type}

    if file_type == 'json':
        with open(file, encoding='utf-8') as fp:
            try:
                json_data = json.load(fp)
            except ValueError:
                raise APIException('The file looks like invalid json')

            schema_ocds = SchemaOCDS(schema_version, json_data, cache_schema=cache_schema)

            if schema_ocds.invalid_version_data:
                msg = '\033[1;31mThe schema version in your data is not valid. Accepted values: {}\033[1;m'
                raise APIException(msg.format(str(list(schema_ocds.version_choices.keys()))))
            if schema_ocds.extensions:
                schema_ocds.create_extended_release_schema_file(output_dir, "")

            url = schema_ocds.extended_schema_file or schema_ocds.release_schema_url

            if convert:
                context.update(convert_json(
                    output_dir, '', file, schema_url=url, flatten=True, cache=False)
                )

    else:
        metatab_schema_url = SchemaOCDS(select_version='1.1').release_pkg_schema_url
        metatab_data = get_spreadsheet_meta_data(output_dir, file, metatab_schema_url, file_type=file_type)
        schema_ocds = SchemaOCDS(schema_version, release_data=metatab_data, cache_schema=cache_schema)

        if schema_ocds.invalid_version_data:
            msg = '\033[1;31mThe schema version in your data is not valid. Accepted values: {}\033[1;m'
            raise APIException(msg.format(str(list(schema_ocds.version_choices.keys()))))
        if schema_ocds.extensions:
            schema_ocds.create_extended_release_schema_file(output_dir, '')

        url = schema_ocds.extended_schema_file or schema_ocds.release_schema_url
        pkg_url = schema_ocds.release_pkg_schema_url

        context.update(convert_spreadsheet(
            output_dir, '', file, file_type, schema_url=url, pkg_schema_url=pkg_url, cache=False)
        )

        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp)

    context = context_api_transform(
        common_checks_ocds(context, output_dir, json_data, schema_ocds, api=True, cache=False)
    )

    if file_type == 'xlsx':
        # Remove unwanted files in the output
        # TODO: can we do this by no writing the files in the first place?
        os.remove(os.path.join(output_dir, 'heading_source_map.json'))
        os.remove(os.path.join(output_dir, 'cell_source_map.json'))

    return context
