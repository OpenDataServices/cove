from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from cove.input.models import SuppliedData
import os
import json
import logging
import functools
from django.db.models.aggregates import Count
from django.utils import timezone
from django.http import Http404
from datetime import timedelta
import cove.lib.common as common
import cove.lib.ocds as ocds
import cove.lib.threesixtygiving as threesixtygiving
from cove.lib.converters import convert_spreadsheet, convert_json
from cove.lib.exceptions import CoveInputDataError

logger = logging.getLogger(__name__)


class CoveWebInputDataError(CoveInputDataError):
    """
    An error that we think is due to the data input by the user, rather than a
    bug in the application. Returns nicely rendered HTML. Depends on Django
    """
    def __init__(self, context=None):
        if context:
            self.context = context

    @staticmethod
    def error_page(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                return func(request, *args, **kwargs)
            except CoveInputDataError as err:
                return render(request, 'error.html', context=err.context)
        return wrapper


class UnrecognisedFileType(CoveInputDataError):
    context = {
        'sub_title': _("Sorry we can't process that data"),
        'link': 'cove:index',
        'link_text': _('Try Again'),
        'msg': _('We did not recognise the file type.\n\nWe can only process json, csv and xlsx files.')
    }


def get_file_type(django_file):
    name = django_file.name.lower()
    if name.endswith('.json'):
        return 'json'
    elif name.endswith('.xlsx'):
        return 'xlsx'
    elif name.endswith('.csv'):
        return 'csv'
    else:
        first_byte = django_file.read(1)
        if first_byte in [b'{', b'[']:
            return 'json'
        else:
            raise UnrecognisedFileType


@CoveWebInputDataError.error_page
def explore(request, pk):
    if request.current_app == 'cove-resourceprojects':
        import cove.dataload.views
        return cove.dataload.views.data(request, pk)

    try:
        data = SuppliedData.objects.get(pk=pk)
    except (SuppliedData.DoesNotExist, ValueError):  # Catches: Primary key does not exist, and, badly formed hexadecimal UUID string
        return render(request, 'error.html', {
            'sub_title': _('Sorry, the page you are looking for is not available'),
            'link': 'cove:index',
            'link_text': _('Go to Home page'),
            'msg': _("We don't seem to be able to find the data you requested.")
            }, status=404)

    try:
        data.original_file.file.name
    except FileNotFoundError:
        return render(request, 'error.html', {
            'sub_title': _('Sorry, the page you are looking for is not available'),
            'link': 'cove:index',
            'link_text': _('Go to Home page'),
            'msg': _('The data you were hoping to explore no longer exists.\n\nThis is because all data suplied to this website is automatically deleted after 7 days, and therefore the analysis of that data is no longer available.')
        }, status=404)

    file_type = get_file_type(data.original_file)
    context = {
        "original_file": {
            "url": data.original_file.url,
            "size": data.original_file.size
        },
        "current_url": request.build_absolute_uri(),
        "source_url": data.source_url,
        "form_name": data.form_name,
        "created_datetime": data.created.strftime("%A, %d %B %Y %I:%M%p %Z"),
        "created_date": data.created.strftime("%A, %d %B %Y"),
    }
    
    schema_name = request.cove_config['schema_name']
    schema_version = data.schema_version or request.cove_config['schema_version']
    schema_version_choices = request.cove_config['schema_version_choices']
    schema_user_choice = None
    replace_conversion = False

    if 'version' in request.POST and request.POST['version'] != data.schema_version:
        schema_user_choice = request.POST.get('version')
        if schema_user_choice in schema_version_choices:
            schema_version = schema_user_choice
            replace_conversion = True
        else:
            # This shouldn't really happen unless the user resends manually
            # the POST request with random data.
            raise CoveInputDataError(context={
                'sub_title': _("Something unexpected happened"),
                'link': 'cove:explore',
                'link_args': pk,
                'link_text': _('Try Again'),
                'msg': _('We think you tried to run your data against an unreconigsed version of the schema.\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span> <strong>Error message:</strong> <em>{}</em> is not a valid choice for the schema version'.format(schema_user_choice)),
                'error': '{} is not a valid schema version'.format(schema_user_choice)
            })

    if request.current_app == 'cove-ocds':
        schema_url = schema_version_choices[schema_version]
        context.update({
            "data_uuid": pk,
            "version_choices": [version for version, url in schema_version_choices.items()]
        })
    else:
        schema_url = request.cove_config['schema_url']

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
                    'msg': _('We think you tried to upload a JSON file, but it is not well formed JSON.\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span> <strong>Error message:</strong> {}'.format(err)),
                    'error': format(err)
                })
        if request.current_app == 'cove-ocds' and not schema_user_choice:
            try:
                version_field = json_data.get('version')
                if version_field:
                    schema_version = version_field
                    schema_url = schema_version_choices[schema_version]
            except AttributeError:
                pass
        if request.current_app == 'cove-ocds' and 'records' in json_data:
            context['conversion'] = None
        else:
            converted_path = os.path.join(data.upload_dir(), 'flattened')
            # Replace the spreadsheet conversion only if it exists, ie. do not
            # create a conversion if there wasn't one requested by the user.
            if not os.path.exists(converted_path + '.xlsx'):
                replace_conversion = False
            context.update(convert_json(request, data, schema_url=schema_url, replace=replace_conversion))
    else:
        # Always replace json conversion when user chooses a different schema version.
        context.update(convert_spreadsheet(request, data, file_type, schema_url=schema_url, replace=replace_conversion))
        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp)

    if request.current_app == 'cove-ocds':
        schema_name = schema_name['record'] if 'records' in json_data else schema_name['release']
        context.update({
            "version_used": schema_version,
        })

    if schema_url:
        additional_fields = sorted(common.get_counts_additional_fields(schema_url, schema_name, json_data, context, request.current_app))
        context.update({
            'data_only': additional_fields,
            'additional_fields_count': sum(item[2] for item in additional_fields)
        })

    cell_source_map = {}
    heading_source_map = {}
    if file_type != 'json':  # Assume it is csv or xlsx
        with open(os.path.join(data.upload_dir(), 'cell_source_map.json')) as cell_source_map_fp:
            cell_source_map = json.load(cell_source_map_fp)

        with open(os.path.join(data.upload_dir(), 'heading_source_map.json')) as heading_source_map_fp:
            heading_source_map = json.load(heading_source_map_fp)

    validation_errors_path = os.path.join(data.upload_dir(), 'validation_errors-2.json')
    if os.path.exists(validation_errors_path) and not replace_conversion:
        with open(validation_errors_path) as validiation_error_fp:
            validation_errors = json.load(validiation_error_fp)
    else:
        validation_errors = common.get_schema_validation_errors(json_data, schema_url, schema_name, request.current_app, cell_source_map, heading_source_map) if schema_url else None
        with open(validation_errors_path, 'w+') as validiation_error_fp:
            validiation_error_fp.write(json.dumps(validation_errors))

    context.update({
        'file_type': file_type,
        'schema_url': schema_url + schema_name,
        'validation_errors': sorted(validation_errors.items()),
        'validation_errors_count': sum(len(value) for value in validation_errors.values()),
        'json_data': json_data,  # Pass the JSON data to the template so we can display values that need little processing
        'first_render': not data.rendered,
        'common_error_types': []
    })

    view = 'explore.html'
    if request.current_app == 'cove-ocds':
        if 'records' in json_data:
            context['records_aggregates'] = ocds.get_records_aggregates(json_data, ignore_errors=bool(validation_errors))
            view = 'explore_ocds-record.html'
        else:
            context['releases_aggregates'] = ocds.get_releases_aggregates(json_data, ignore_errors=bool(validation_errors))
            view = 'explore_ocds-release.html'
    elif request.current_app == 'cove-360':
        context['grants_aggregates'] = threesixtygiving.get_grants_aggregates(json_data)
        context['additional_checks'] = threesixtygiving.run_additional_checks(json_data, cell_source_map)
        context['additional_checks_count'] = len(context['additional_checks']) + (1 if context['data_only'] else 0)
        context['common_error_types'] = ['uri', 'date-time', 'required', 'enum', 'integer', 'string']
        view = 'explore_360.html'

    if not data.rendered:
        data.rendered = True
    data.schema_version = schema_version
    data.save()

    rendered_response = render(request, view, context)
    return rendered_response


def stats(request):
    query = SuppliedData.objects.filter(current_app=request.current_app)
    by_form = query.values('form_name').annotate(Count('id'))
    return render(request, 'stats.html', {
        'uploaded': query.count(),
        'total_by_form': {x['form_name']: x['id__count'] for x in by_form},
        'upload_by_time_by_form': [(
            num_days,
            query.filter(created__gt=timezone.now() - timedelta(days=num_days)).count(),
            {x['form_name']: x['id__count'] for x in by_form.filter(created__gt=timezone.now() - timedelta(days=num_days))}
        ) for num_days in [1, 7, 30]],
    })


def common_errors(request):
    if request.current_app == 'cove-360':
        return render(request, 'common_errors_360.html')
    raise Http404('Common error page does not exist')
