import os
from flattentool.json_input import BadlyFormedJSONError
import logging
import shutil
import warnings
import flattentool
import json
import flattentool.exceptions

from django.utils.translation import ugettext_lazy as _

from cove.lib.exceptions import CoveInputDataError

logger = logging.getLogger(__name__)


def filter_conversion_warnings(conversion_warnings):
    out = []
    for w in conversion_warnings:
        if w.category is flattentool.exceptions.DataErrorWarning:
            out.append(str(w.message))
        else:
            logger.warn(w)
    return out


def convert_spreadsheet(request, data, file_type, schema_url, replace):
    context = {}
    converted_path = os.path.join(data.upload_dir(), 'unflattened.json')
    cell_source_map_path = os.path.join(data.upload_dir(), 'cell_source_map.json')
    heading_source_map_path = os.path.join(data.upload_dir(), 'heading_source_map.json')
    encoding = 'utf-8'
    # 360 still uses request.cove_config['schema_url']
    schema_url = schema_url or request.cove_config['schema_url']

    if file_type == 'csv':
        # flatten-tool expects a directory full of CSVs with file names
        # matching what xlsx titles would be.
        # If only one upload file is specified, we rename it and move into
        # a new directory, such that it fits this pattern.
        input_name = os.path.join(data.upload_dir(), 'csv_dir')
        os.makedirs(input_name, exist_ok=True)
        destination = os.path.join(input_name, request.cove_config['root_list_path'] + '.csv')
        shutil.copy(data.original_file.file.name, destination)
        try:
            with open(destination, encoding='utf-8') as main_sheet_file:
                main_sheet_file.read()
        except UnicodeDecodeError:
            try:
                with open(destination, encoding='cp1252') as main_sheet_file:
                    main_sheet_file.read()
                encoding = 'cp1252'
            except UnicodeDecodeError:
                encoding = 'latin_1'
    else:
        input_name = data.original_file.file.name

    try:
        conversion_warning_cache_path = os.path.join(data.upload_dir(), 'conversion_warning_messages.json')
        if not os.path.exists(converted_path) or not os.path.exists(cell_source_map_path) or replace:
            with warnings.catch_warnings(record=True) as conversion_warnings:
                flattentool.unflatten(
                    input_name,
                    output_name=converted_path,
                    input_format=file_type,
                    root_list_path=request.cove_config['root_list_path'],
                    root_id=request.cove_config['root_id'],
                    schema=schema_url + request.cove_config['item_schema_name'],
                    convert_titles=True,
                    encoding=encoding,
                    cell_source_map=cell_source_map_path,
                    heading_source_map=heading_source_map_path,
                )
                context['conversion_warning_messages'] = filter_conversion_warnings(conversion_warnings)
            with open(conversion_warning_cache_path, 'w+') as fp:
                json.dump(context['conversion_warning_messages'], fp)
        elif os.path.exists(conversion_warning_cache_path):
            with open(conversion_warning_cache_path) as fp:
                context['conversion_warning_messages'] = json.load(fp)

        context['converted_file_size'] = os.path.getsize(converted_path)
    except Exception as err:
        logger.exception(err, extra={
            'request': request,
            })
        raise CoveInputDataError({
            'sub_title': _("Sorry we can't process that data"),
            'link': 'cove:index',
            'link_text': _('Try Again'),
            'msg': _('We think you tried to supply a spreadsheet, but we failed to convert it to JSON.\n\nError message: {}'.format(repr(err)))
        })

    context.update({
        'conversion': 'unflatten',
        'converted_path': converted_path,
        'converted_url': '{}/unflattened.json'.format(data.upload_url()),
        "csv_encoding": encoding
    })
    return context


def convert_json(request, data, schema_url, replace):
    context = {}
    converted_path = os.path.join(data.upload_dir(), 'flattened')
    # cove-360 still uses request.cove_config['schema_url']
    schema_url = schema_url or request.cove_config['schema_url']

    flatten_kwargs = dict(
        output_name=converted_path,
        main_sheet_name=request.cove_config['root_list_path'],
        root_list_path=request.cove_config['root_list_path'],
        root_id=request.cove_config['root_id'],
        schema=schema_url + request.cove_config['item_schema_name'],
    )

    try:
        conversion_warning_cache_path = os.path.join(data.upload_dir(), 'conversion_warning_messages.json')
        if not os.path.exists(converted_path + '.xlsx') or replace:
            with warnings.catch_warnings(record=True) as conversion_warnings:
                if request.POST.get('flatten') or replace:
                    flattentool.flatten(data.original_file.file.name, **flatten_kwargs)
                else:
                    return {'conversion': 'flattenable'}
                context['conversion_warning_messages'] = filter_conversion_warnings(conversion_warnings)
            with open(conversion_warning_cache_path, 'w+') as fp:
                json.dump(context['conversion_warning_messages'], fp)
        elif os.path.exists(conversion_warning_cache_path):
            with open(conversion_warning_cache_path) as fp:
                context['conversion_warning_messages'] = json.load(fp)
        context['converted_file_size'] = os.path.getsize(converted_path + '.xlsx')

        conversion_warning_cache_path_titles = os.path.join(data.upload_dir(), 'conversion_warning_messages_titles.json')

        if request.cove_config['convert_titles']:
            with warnings.catch_warnings(record=True) as conversion_warnings_titles:
                flatten_kwargs.update(dict(
                    output_name=converted_path + '-titles',
                    use_titles=True
                ))
                if not os.path.exists(converted_path + '-titles.xlsx') or replace:
                    flattentool.flatten(data.original_file.file.name, **flatten_kwargs)
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
            'link': 'cove:index',
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
        'converted_url': '{}/flattened'.format(data.upload_url())
    })
    return context
