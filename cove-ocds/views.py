import json
import logging
import os

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from lib.ocds import get_records_aggregates, get_releases_aggregates
from cove.lib.common import SchemaOCDS, get_additional_codelist_values
from cove.lib.converters import convert_spreadsheet, convert_json
from cove.lib.exceptions import CoveInputDataError, CoveWebInputDataError
from cove.views import explore_data_context, common_checks_context


logger = logging.getLogger(__name__)


def common_checks_ocds(context, db_data, json_data, schema_obj):
    schema_name = schema_obj.release_pkg_schema_name
    if 'records' in json_data:
        schema_name = schema_obj.record_pkg_schema_name
    common_checks = common_checks_context(db_data, json_data, schema_obj, schema_name, context, fields_regex=True)
    validation_errors = common_checks['context']['validation_errors']

    context.update(common_checks['context'])

    if schema_name == 'record-package-schema.json':
        context['records_aggregates'] = get_records_aggregates(json_data, ignore_errors=bool(validation_errors))
    else:
        schema_codelist = request.cove_config['schema_codelists'].get(schema_obj.version)
        additional_codelist_values = get_additional_codelist_values(schema_obj, schema_codelist, json_data)
        closed_codelist_values = {key: value for key, value in additional_codelist_values.items() if not value['isopen']}
        open_codelist_values = {key: value for key, value in additional_codelist_values.items() if value['isopen']}

        context.update({
            context['releases_aggregates']: get_releases_aggregates(json_data, ignore_errors=bool(validation_errors)),
            context['additional_closed_codelist_values']: closed_codelist_values,
            context['additional_open_codelist_values']: open_codelist_values
        })

    return context


@CoveWebInputDataError.error_page
def explore_ocds(request, pk, data):
    post_version_choice = request.POST.get('version')
    replace = False
    context, db_data = explore_data_context(request, pk)
    file_type = context['file_type']

    if file_type == 'json':
        # open the data first so we can inspect for record package
        with open(data.original_file.file.name, encoding='utf-8') as fp:
            try:
                json_data = json.load(fp)
            except ValueError as err:
                raise CoveInputDataError(context={
                    'sub_title': _("Sorry we can't process that data"),
                    'link': 'cove:index',
                    'link_text': _('Try Again'),
                    'msg': _('We think you tried to upload a JSON file, but it is not well formed JSON.'
                             '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                             '</span> <strong>Error message:</strong> {}'.format(err)),
                    'error': format(err)
                })

            select_version = post_version_choice or data.schema_version
            schema_ocds = SchemaOCDS(select_version=select_version, release_data=json_data)

            if schema_ocds.invalid_version_argument:
                # This shouldn't really happen unless the user resends manually
                # the POST request with random data.
                raise CoveInputDataError(context={
                    'sub_title': _("Something unexpected happened"),
                    'link': 'cove:explore',
                    'link_args': pk,
                    'link_text': _('Try Again'),
                    'msg': _('We think you tried to run your data against an unrecognised version of '
                             'the schema.\n\n<span class="glyphicon glyphicon-exclamation-sign" '
                             'aria-hidden="true"></span> <strong>Error message:</strong> <em>{}</em> is '
                             'not a recognised choice for the schema version'.format(post_version_choice)),
                    'error': _('{} is not a valid schema version'.format(post_version_choice))
                })
            if schema_ocds.invalid_version_data:
                raise CoveInputDataError(context={
                    'sub_title': _("Wrong schema version"),
                    'link': 'cove:index',
                    'link_text': _('Try Again'),
                    'msg': _('The value for the <em>"version"</em> field in your data is not a recognised '
                             'OCDS schema version.\n\n<span class="glyphicon glyphicon-exclamation-sign" '
                             'aria-hidden="true"></span> <strong>Error message: </strong> <em>{}</em> '
                             'is not a recognised schema version choice'.format(json_data.get('version'))),
                    'error': _('{} is not a valid schema version'.format(json_data.get('version')))
                })

            if 'records' in json_data:
                context['conversion'] = None
            else:
                converted_path = os.path.join(data.upload_dir(), 'flattened')
                validation_errors_path = os.path.join(data.upload_dir(), 'validation_errors-2.json')

                # Replace the spreadsheet conversion only if it exists already.
                if os.path.exists(converted_path + '.xlsx') and schema_ocds.version != data.schema_version:
                    replace = True
                    if os.path.exists(validation_errors_path):
                        os.remove(validation_errors_path)

                url = schema_ocds.release_schema_url
                if schema_ocds.extensions:
                    schema_ocds.get_release_schema_obj()
                    if schema_ocds.extended:
                        schema_ocds.create_extended_release_schema_file(data.upload_dir(), data.upload_url())
                        url = schema_ocds.extended_schema_file

                context.update(convert_json(request, data, url, replace=replace))

    else:
        select_version = post_version_choice or data.schema_version
        schema_ocds = SchemaOCDS(select_version=select_version)
        # Replace json conversion when user chooses a different schema version.
        if data.schema_version and schema_ocds.version != data.schema_version:
            replace = True
        context.update(convert_spreadsheet(request, data, file_type, schema_ocds.release_schema_url, replace=replace))
        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp)

    template = 'explore_ocds-record.html' if 'records' in json_data else 'explore_ocds-release.html'
    context = common_checks_ocds(context, db_data, json_data, schema_ocds)
    return render(request, template, context)
