import json
import logging
import os
import shutil
import warnings

import flattentool
import flattentool.exceptions
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from flattentool.json_input import BadlyFormedJSONError

from cove.lib.exceptions import CoveInputDataError, cove_spreadsheet_conversion_error

logger = logging.getLogger(__name__)
config = settings.COVE_CONFIG


def filter_conversion_warnings(conversion_warnings):
    out = []
    for w in conversion_warnings:
        if w.category is flattentool.exceptions.DataErrorWarning:
            out.append(str(w.message))
        else:
            logger.warn(w)
    return out


@cove_spreadsheet_conversion_error
def convert_spreadsheet(upload_dir, upload_url, file_name, file_type, schema_url=None, pkg_schema_url=None,
                        metatab_name='Meta', replace=False, xml=False, cache=True):
    context = {}
    if xml:
        output_file = 'unflattened.xml'
        converted_path = os.path.join(upload_dir, 'unflattened.xml')
    else:
        output_file = 'unflattened.json'
        converted_path = os.path.join(upload_dir, 'unflattened.json')
    cell_source_map_path = os.path.join(upload_dir, 'cell_source_map.json')
    heading_source_map_path = os.path.join(upload_dir, 'heading_source_map.json')
    encoding = 'utf-8-sig'

    if file_type == 'csv':
        # flatten-tool expects a directory full of CSVs with file names
        # matching what xlsx titles would be.
        # If only one upload file is specified, we rename it and move into
        # a new directory, such that it fits this pattern.
        input_name = os.path.join(upload_dir, 'csv_dir')
        os.makedirs(input_name, exist_ok=True)
        destination = os.path.join(input_name, config['root_list_path'] + '.csv')
        shutil.copy(file_name, destination)
        try:
            with open(destination, encoding='utf-8-sig') as main_sheet_file:
                main_sheet_file.read()
        except UnicodeDecodeError:
            try:
                with open(destination, encoding='cp1252') as main_sheet_file:
                    main_sheet_file.read()
                encoding = 'cp1252'
            except UnicodeDecodeError:
                encoding = 'latin_1'
    else:
        input_name = file_name

    flattentool_options = {
        'output_name': converted_path,
        'input_format': file_type,
        'root_list_path': config['root_list_path'],
        'encoding': encoding,
        'cell_source_map': cell_source_map_path,
        'heading_source_map': heading_source_map_path,
        'metatab_schema': pkg_schema_url,
        'metatab_name': metatab_name,
        'metatab_vertical_orientation': True
    }

    if xml:
        flattentool_options['xml'] = True
        flattentool_options['id_name'] = config.get('id_name', 'id')
    else:
        flattentool_options.update({
            'schema': schema_url,
            'convert_titles': True,
            'root_id': config['root_id'],
        })

    conversion_warning_cache_path = os.path.join(upload_dir, 'conversion_warning_messages.json')
    if not os.path.exists(converted_path) or not os.path.exists(cell_source_map_path) or replace:
        with warnings.catch_warnings(record=True) as conversion_warnings:
            flattentool.unflatten(
                input_name,
                **flattentool_options
            )
            context['conversion_warning_messages'] = filter_conversion_warnings(conversion_warnings)

        if cache:
            with open(conversion_warning_cache_path, 'w+') as fp:
                json.dump(context['conversion_warning_messages'], fp)

    elif os.path.exists(conversion_warning_cache_path):
        with open(conversion_warning_cache_path) as fp:
            context['conversion_warning_messages'] = json.load(fp)

    context['converted_file_size'] = os.path.getsize(converted_path)

    context.update({
        'conversion': 'unflatten',
        'converted_path': converted_path,
        'converted_url': '{}{}{}'.format(upload_url, '' if upload_url.endswith('/') else '/', output_file),
        "csv_encoding": encoding
    })
    return context


def convert_json(upload_dir, upload_url, file_name, schema_url=None, replace=False, request=None, flatten=False, cache=True, xml=False):
    context = {}
    converted_path = os.path.join(upload_dir, 'flattened')

    flatten_kwargs = dict(
        output_name=converted_path,
        main_sheet_name=config['root_list_path'],
        root_list_path=config['root_list_path'],
        root_id=config['root_id'],
        schema=schema_url
    )

    if xml:
        flatten_kwargs['xml'] = True
        flatten_kwargs['id_name'] = config.get('id_name', 'id')

    try:
        conversion_warning_cache_path = os.path.join(upload_dir, 'conversion_warning_messages.json')
        conversion_exists = os.path.exists(converted_path + '.xlsx')
        if not conversion_exists or replace:
            with warnings.catch_warnings(record=True) as conversion_warnings:
                if flatten or (replace and conversion_exists):
                    flattentool.flatten(file_name, **flatten_kwargs)
                else:
                    return {'conversion': 'flattenable'}
                context['conversion_warning_messages'] = filter_conversion_warnings(conversion_warnings)

            if cache:
                with open(conversion_warning_cache_path, 'w+') as fp:
                    json.dump(context['conversion_warning_messages'], fp)

        elif os.path.exists(conversion_warning_cache_path):
            with open(conversion_warning_cache_path) as fp:
                context['conversion_warning_messages'] = json.load(fp)

        context['converted_file_size'] = os.path.getsize(converted_path + '.xlsx')
        conversion_warning_cache_path_titles = os.path.join(upload_dir, 'conversion_warning_messages_titles.json')

        if config['convert_titles']:
            with warnings.catch_warnings(record=True) as conversion_warnings_titles:
                flatten_kwargs.update(dict(
                    output_name=converted_path + '-titles',
                    use_titles=True
                ))
                if not os.path.exists(converted_path + '-titles.xlsx') or replace:
                    flattentool.flatten(file_name, **flatten_kwargs)
                    context['conversion_warning_messages_titles'] = filter_conversion_warnings(conversion_warnings_titles)
                    with open(conversion_warning_cache_path_titles, 'w+') as fp:
                        json.dump(context['conversion_warning_messages_titles'], fp)
                elif os.path.exists(conversion_warning_cache_path_titles):
                    with open(conversion_warning_cache_path_titles) as fp:
                        context['conversion_warning_messages_titles'] = json.load(fp)

            context['converted_file_size_titles'] = os.path.getsize(converted_path + '-titles.xlsx')

    except BadlyFormedJSONError as err:
        raise CoveInputDataError(context={
            'sub_title': _("Sorry we can't process that data"),
            'link': 'index',
            'link_text': _('Try Again'),
            'msg': _('We think you tried to upload a JSON file, but it is not well formed JSON.\n\nError message: {}'.format(err))
        })
    except Exception as err:
        logger.exception(err, extra={
            'request': request,
            })
        return {
            'conversion': 'flatten',
            'conversion_error': repr(err)
        }
    context.update({
        'conversion': 'flatten',
        'converted_path': converted_path,
        'converted_url': '{}{}flattened'.format(upload_url, '' if upload_url.endswith('/') else '/')
    })
    return context
