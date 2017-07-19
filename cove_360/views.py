import json
import logging

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from . lib.threesixtygiving import get_grants_aggregates, run_additional_checks
from . lib.schema import Schema360
from cove.lib.tools import datetime_or_date
from cove.lib.converters import convert_spreadsheet, convert_json
from cove.lib.exceptions import CoveInputDataError, cove_web_input_error
from cove.views import explore_data_context, common_checks_context

logger = logging.getLogger(__name__)


def common_checks_360(context, db_data, json_data, schema_obj):
    schema_name = schema_obj.release_pkg_schema_name
    checkers = {'date-time': (datetime_or_date, ValueError)}
    common_checks = common_checks_context(db_data, json_data, schema_obj, schema_name, context, extra_checkers=checkers)
    cell_source_map = common_checks['cell_source_map']
    additional_checks = run_additional_checks(json_data, cell_source_map, ignore_errors=True)

    context.update(common_checks['context'])
    context.update({
        'grants_aggregates': get_grants_aggregates(json_data, ignore_errors=True),
        'additional_checks': additional_checks,
        'additional_checks_count': len(additional_checks) + (1 if context['data_only'] else 0),
        'common_error_types': ['uri', 'date-time', 'required', 'enum', 'integer', 'string']
    })

    return context


@cove_web_input_error
def explore_360(request, pk, template='cove_360/explore.html'):
    schema_360 = Schema360()
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error
    file_type = context['file_type']

    if file_type == 'json':
        # open the data first so we can inspect for record package
        with open(db_data.original_file.file.name, encoding='utf-8') as fp:
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

            if not isinstance(json_data, dict):
                raise CoveInputDataError(context={
                    'sub_title': _("Sorry we can't process that data"),
                    'link': 'index',
                    'link_text': _('Try Again'),
                    'msg': _('360Giving JSON should have an object as the top level, the JSON you supplied does not.'),
                })

            context.update(convert_json(request, db_data, schema_360.release_schema_url))
    else:
        context.update(convert_spreadsheet(request, db_data, file_type, schema_360.release_schema_url))
        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp)

    context = common_checks_360(context, db_data, json_data, schema_360)
    return render(request, template, context)


def common_errors(request):
    return render(request, 'cove_360/common_errors.html')
