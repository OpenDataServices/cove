import json
import logging
from decimal import Decimal
import functools

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html

from . lib.schema import Schema360
from . lib.threesixtygiving import common_checks_360
from . lib.threesixtygiving import TEST_CLASSES
from libcove.lib.converters import convert_spreadsheet, convert_json
from libcove.lib.exceptions import CoveInputDataError
from libcove.config import LibCoveConfig
from django.conf import settings

from cove.views import explore_data_context

logger = logging.getLogger(__name__)


def cove_web_input_error(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except CoveInputDataError as err:
            return render(request, 'error.html', context=err.context)
    return wrapper


@cove_web_input_error
def explore_360(request, pk, template='cove_360/explore.html'):
    schema_360 = Schema360()
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error

    lib_cove_config = LibCoveConfig()
    lib_cove_config.config.update(settings.COVE_CONFIG)

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
                    'sub_title': _("Sorry, we can't process that data"),
                    'link': 'index',
                    'link_text': _('Try Again'),
                    'msg': _(format_html('We think you tried to upload a JSON file, but it is not well formed JSON.'
                             '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                             '</span> <strong>Error message:</strong> {}', err)),
                    'error': format(err)
                })
            if not isinstance(json_data, dict):
                raise CoveInputDataError(context={
                    'sub_title': _("Sorry, we can't process that data"),
                    'link': 'index',
                    'link_text': _('Try Again'),
                    'msg': _('360Giving JSON should have an object as the top level, the JSON you supplied does not.'),
                })

            context.update(convert_json(upload_dir, upload_url, file_name, schema_url=schema_360.release_schema_url,
                                        request=request, flatten=request.POST.get('flatten'),
                                        lib_cove_config=lib_cove_config))

    else:
        context.update(convert_spreadsheet(upload_dir, upload_url, file_name, file_type, lib_cove_config, schema_360.release_schema_url,
                                           schema_360.release_pkg_schema_url))
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
