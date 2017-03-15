import json
import logging

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from . lib import threesixtygiving
from cove.lib.tools import datetime_or_date
from cove.lib.common import Schema360
from cove.lib.converters import convert_spreadsheet, convert_json
from cove.lib.exceptions import CoveInputDataError, CoveWebInputDataError
from cove.views import explore_data_context, common_checks_context

logger = logging.getLogger(__name__)


@CoveWebInputDataError.error_page
def explore_360(request, pk, data, context):
    schema_360 = Schema360()
    context, data = explore_data_context(request, pk)
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
            context.update(convert_json(request, data, schema_url=schema_360.release_schema_url, replace=False))
    else:
        context.update(convert_spreadsheet(request, data, file_type, schema_url=schema_360.release_schema_url, replace=False))
        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp)

    schema_name = schema_360.release_pkg_schema_name

    checkers = {'date-time': (datetime_or_date, ValueError)}
    common_checks = common_checks_context(request, data, json_data, schema_360, schema_name, context, validation_checkers=checkers)
    cell_source_map = common_checks['cell_source_map']

    context.update(common_checks['context'])
    context.update({
        'grants_aggregates': threesixtygiving.get_grants_aggregates(json_data),
        'additional_checks': threesixtygiving.run_additional_checks(json_data, cell_source_map),
        'additional_checks_count': len(context['additional_checks']) + (1 if context['data_only'] else 0),
        'common_error_types': ['uri', 'date-time', 'required', 'enum', 'integer', 'string']
    })

    return render(request, 'explore_360.html', context)


def common_errors(request):
    return render(request, 'common_errors_360.html')
