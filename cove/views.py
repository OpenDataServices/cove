from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from cove.input.models import SuppliedData
import os
import shutil
import json
import logging
import flattentool
import functools
from flattentool.json_input import BadlyFormedJSONError
import requests
from jsonschema.validators import Draft4Validator as validator
from django.db.models.aggregates import Count
from django.utils import timezone
from datetime import timedelta


logger = logging.getLogger(__name__)


def get_releases_aggregates(json_data):
    # Unique ocids & Release dates
    ocids = []
    unique_ocids = []
    release_dates = []
    earliest_release_date = None
    latest_release_date = None
    #table_data = {}
    if 'releases' in json_data:
        for release in json_data['releases']:
            # Gather all the ocids
            if 'ocid' in release:
                ocids.append(release['ocid'])
            
            #Gather all the release dates
            if 'date' in release:
                release_dates.append(release['date'])
 
        # Find unique ocid's
        unique_ocids = set(ocids)
        
        # Get the earliest and latest release dates found
        if release_dates:
            earliest_release_date = min(release_dates)
            latest_release_date = max(release_dates)

    # Number of releases
    count = len(json_data['releases']) if 'releases' in json_data else 0
    
    return {
        'count': count,
        'unique_ocids': unique_ocids,
        'earliest_release_date': earliest_release_date,
        'latest_release_date': latest_release_date,
    }


def get_grants_aggregates(json_data):
    count = len(json_data['grants']) if 'grants' in json_data else 0
    
    ids = []
    unique_ids = []
    if 'grants' in json_data:
        for grant in json_data['grants']:
            # Gather all the ocids
            if 'id' in grant:
                ids.append(grant['id'])
            
        # Find unique ocid's
        unique_ids = set(ids)
    
    return {
        'count': count,
        'unique_ids': unique_ids
    }


def get_schema_validation_errors(json_data, schema_url):
    schema = requests.get(schema_url).json()
    validation_error_list = []
    for n, e in enumerate(validator(schema).iter_errors(json_data)):
        if n >= 100:
            break
        validation_error_list.append(e)
    return validation_error_list
    

class CoveInputDataError(Exception):
    """
    An error that we think is due to the data input by the user, rather than a
    bug in the application.
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
        'msg': _('We did not recognise the file type.\n\nWe can only process json, csv and xlsx files.\n\nIs this a bug? Contact us on code [at] opendataservices.coop')
    }


def get_file_type(django_file):
    if django_file.name.endswith('.json'):
        return 'json'
    elif django_file.name.endswith('.xlsx'):
        return 'xlsx'
    elif django_file.name.endswith('.csv'):
        return 'csv'
    else:
        first_byte = django_file.read(1)
        if first_byte in [b'{', b'[']:
            return 'json'
        else:
            raise UnrecognisedFileType


def convert_json(request, data):
    converted_path = os.path.join(data.upload_dir(), 'flattened')
    flatten_kwargs = dict(
        output_name=converted_path,
        main_sheet_name=request.cove_config['main_sheet_name'],
        root_list_path=request.cove_config['main_sheet_name'],
        root_id=request.cove_config['root_id'],
        schema=request.cove_config['item_schema_url'],
    )
    if request.cove_config['convert_titles']:
        flatten_kwargs.update(dict(
            output_name=converted_path + '-titles',
            use_titles=True
        ))
    try:
        flattentool.flatten(data.original_file.file.name, **flatten_kwargs)
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
    return {
        'conversion': 'flatten',
        'converted_path': converted_path,
        'converted_url': '{}/flattened'.format(data.upload_url())
    }


def convert_spreadsheet(request, data, file_type):
    converted_path = os.path.join(data.upload_dir(), 'unflattened.json')
    if file_type == 'csv':
        # flatten-tool expects a directory full of CSVs with file names
        # matching what xlsx titles would be.
        # If only one upload file is specified, we rename it and move into
        # a new directory, such that it fits this pattern.
        input_name = os.path.join(data.upload_dir(), 'csv_dir')
        os.makedirs(input_name, exist_ok=True)
        shutil.copy(data.original_file.file.name, os.path.join(input_name, request.cove_config['main_sheet_name'] + '.csv'))
    else:
        input_name = data.original_file.file.name
    try:
        flattentool.unflatten(
            input_name,
            output_name=converted_path,
            input_format=file_type,
            main_sheet_name=request.cove_config['main_sheet_name'],
            root_id=request.cove_config['root_id'],
            schema=request.cove_config['item_schema_url'],
            convert_titles=True
        )
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

    return {
        'conversion': 'unflatten',
        'converted_path': converted_path,
        'converted_url': '{}/unflattened.json'.format(data.upload_url())
    }


@CoveInputDataError.error_page
def explore(request, pk):
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

    context = {}

    if file_type == 'json':
        context.update(convert_json(request, data))
        json_path = data.original_file.file.name
    else:
        context.update(convert_spreadsheet(request, data, file_type))
        json_path = context['converted_path']

    with open(json_path, encoding='utf-8') as fp:
        json_data = json.load(fp)
        schema_url = request.cove_config['schema_url']

        context.update({
            'file_type': file_type,
            'schema_url': schema_url,
            'validation_error_list': get_schema_validation_errors(json_data, schema_url) if schema_url else None,
            'json_data': json_data  # Pass the JSON data to the template so we can display values that need little processing
        })

        if request.current_app == 'cove-ocds':
            context['releases_aggregates'] = get_releases_aggregates(json_data)
        elif request.current_app == 'cove-360':
            context['grants_aggregates'] = get_grants_aggregates(json_data)

        return render(request, 'explore.html', context)


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
