import json
import logging
import os
import re

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from . lib.exceptions import raise_invalid_version_argument, raise_invalid_version_data_with_patch
from . lib.ocds import common_checks_ocds
from . lib.schema import SchemaOCDS
from cove.lib.common import get_spreadsheet_meta_data
from cove.lib.converters import convert_spreadsheet, convert_json
from cove.lib.exceptions import CoveInputDataError, cove_web_input_error
from cove.views import explore_data_context


logger = logging.getLogger(__name__)


@cove_web_input_error
def explore_ocds(request, pk):
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error

    upload_dir = db_data.upload_dir()
    upload_url = db_data.upload_url()
    file_name = db_data.original_file.file.name
    file_type = context['file_type']

    post_version_choice = request.POST.get('version')
    replace = False
    validation_errors_path = os.path.join(upload_dir, 'validation_errors-2.json')

    if file_type == 'json':
        # open the data first so we can inspect for record package
        with open(file_name, encoding='utf-8') as fp:
            try:
                json_data = json.load(fp)
            except ValueError as err:
                raise CoveInputDataError(context={
                    'sub_title': _("Sorry we can't process that data"),
                    'link': 'index',
                    'link_text': _('Try Again'),
                    'msg': _('We think you tried to upload a JSON file, but it is not well formed JSON.'
                             '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                             '</span> <strong>Error message:</strong> {}'.format(err)),
                    'error': format(err)
                })

            select_version = post_version_choice or db_data.schema_version
            schema_ocds = SchemaOCDS(select_version=select_version, release_data=json_data)

            if schema_ocds.invalid_version_argument:
                # This shouldn't happen unless the user sends random POST data.
                raise_invalid_version_argument(pk, post_version_choice)
            if schema_ocds.invalid_version_data:
                version_in_data = json_data.get('version')
                if isinstance(version_in_data, str) and re.compile('^\d+\.\d+\.\d+$').match(version_in_data):
                    raise_invalid_version_data_with_patch(version_in_data)
                else:
                    if not isinstance(version_in_data, str):
                        version_in_data = '{} (it must be a string)'.format(str(version_in_data))
                    context['unrecognized_version_data'] = version_in_data

            # Replace the spreadsheet conversion only if it exists already.
            if schema_ocds.version != db_data.schema_version:
                replace = True

            if 'records' in json_data:
                context['conversion'] = None
            else:
                converted_path = os.path.join(upload_dir, 'flattened')

                if schema_ocds.extensions:
                    schema_ocds.create_extended_release_schema_file(upload_dir, upload_url)
                url = schema_ocds.extended_schema_file or schema_ocds.release_schema_url

                replace_converted = replace and os.path.exists(converted_path + '.xlsx')
                context.update(convert_json(upload_dir, upload_url, file_name, schema_url=url, replace=replace_converted,
                                            request=request, flatten=request.POST.get('flatten')))

    else:
        # Use the lowest release pkg schema version accepting 'version' field
        metatab_schema_url = SchemaOCDS(select_version='1.1').release_pkg_schema_url
        metatab_data = metatab_data = get_spreadsheet_meta_data(upload_dir, file_name, metatab_schema_url, file_type)
        if 'version' not in metatab_data:
            metatab_data['version'] = '1.0'

        select_version = post_version_choice or db_data.schema_version

        schema_ocds = SchemaOCDS(select_version=select_version, release_data=metatab_data)
        if schema_ocds.invalid_version_argument:
            # This shouldn't happen unless the user sends random POST data.
            raise_invalid_version_argument(pk, post_version_choice)
        if schema_ocds.invalid_version_data:
            version_in_data = metatab_data.get('version')
            if re.compile('^\d+\.\d+\.\d+$').match(version_in_data):
                raise_invalid_version_data_with_patch(version_in_data)
            else:
                context['unrecognized_version_data'] = version_in_data

        # Replace json conversion when user chooses a different schema version.
        if db_data.schema_version and schema_ocds.version != db_data.schema_version:
            replace = True

        if schema_ocds.extensions:
            schema_ocds.create_extended_release_schema_file(upload_dir, upload_url)
        url = schema_ocds.extended_schema_file or schema_ocds.release_schema_url
        pkg_url = schema_ocds.release_pkg_schema_url

        context.update(convert_spreadsheet(upload_dir, upload_url, file_name, file_type, schema_url=url,
                                           pkg_schema_url=pkg_url, replace=replace))

        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp)

    if replace:
        if os.path.exists(validation_errors_path):
            os.remove(validation_errors_path)

    context = common_checks_ocds(context, upload_dir, json_data, schema_ocds)
    context['first_render'] = not db_data.rendered
    schema_version = getattr(schema_ocds, 'version', None)

    if schema_version:
        db_data.schema_version = schema_version
    if not db_data.rendered:
        db_data.rendered = True

    db_data.save()

    if 'records' in json_data:
        template = 'cove_ocds/explore_record.html'
        if hasattr(json_data, 'get') and hasattr(json_data.get('records'), '__iter__'):
            context['records'] = json_data['records']
        else:
            context['records'] = []
    else:
        template = 'cove_ocds/explore_release.html'
        if hasattr(json_data, 'get') and hasattr(json_data.get('releases'), '__iter__'):
            context['releases'] = json_data['releases']
        else:
            context['releases'] = []

    return render(request, template, context)
