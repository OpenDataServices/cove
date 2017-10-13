import json
import logging
from decimal import Decimal

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from . lib.schema import Schema360
from . lib.threesixtygiving import common_checks_360
from . lib.threesixtygiving import TEST_CLASSES
from cove.lib.converters import convert_spreadsheet, convert_json
from cove.lib.exceptions import CoveInputDataError, cove_web_input_error
from cove.views import explore_data_context

logger = logging.getLogger(__name__)


@cove_web_input_error
def explore_360(request, pk, template='cove_360/explore.html'):
    schema_360 = Schema360()
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error

    upload_dir = db_data.upload_dir()
    upload_url = db_data.upload_url()
    file_name = db_data.original_file.file.name
    file_type = context['file_type']

    if file_type == 'json':
        # open the data first so we can inspect for record package
        with open(file_name, encoding='utf-8') as fp:
            try:
                json_data = json.load(fp, parse_float=Decimal)
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

            context.update(convert_json(upload_dir, upload_url, file_name, schema_url=schema_360.release_schema_url,
                                        request=request, flatten=request.POST.get('flatten')))

    else:
        context.update(convert_spreadsheet(upload_dir, upload_url, file_name, file_type, schema_360.release_schema_url, schema_360.release_pkg_schema_url))
        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp, parse_float=Decimal)

    context = common_checks_360(context, upload_dir, json_data, schema_360)

    if hasattr(json_data, 'get') and hasattr(json_data.get('grants'), '__iter__'):
        context['grants'] = json_data['grants']
    else:
        context['grants'] = []

    context['first_render'] = not db_data.rendered
    if not db_data.rendered:
        db_data.rendered = True
    db_data.save()

    return render(request, template, context)


def common_errors(request):
    return render(request, 'cove_360/common_errors.html')


def additional_checks(request):
    context = {}
    context["checks"] = [{**check.check_text, 'desc': check.__doc__} for check in TEST_CLASSES]
    return render(request, 'cove_360/additional_checks.html', context)
