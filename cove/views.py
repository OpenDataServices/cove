from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from cove.input.models import SuppliedData
import os
from collections import OrderedDict
import shutil
import json
import jsonref
import logging
import flattentool
import functools
import collections
import strict_rfc3339
import datetime
from flattentool.json_input import BadlyFormedJSONError
from flattentool.schema import get_property_type_set
import requests
from jsonschema.validators import Draft4Validator as validator
from jsonschema.exceptions import ValidationError
from jsonschema import FormatChecker
from django.db.models.aggregates import Count
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


uniqueItemsValidator = validator.VALIDATORS.pop("uniqueItems")


def uniqueIds(validator, uI, instance, schema):
    if (
        uI and
        validator.is_type(instance, "array")
    ):
        non_unique_ids = set()
        all_ids = set()
        for item in instance:
            try:
                item_id = item.get('id')
            except AttributeError:
                ##if item is not a dict
                item_id = None
            if item_id:
                if item_id in all_ids:
                    non_unique_ids.add(item_id)
                all_ids.add(item_id)
            else:
                ## if there is any item without an id key, or the item is not a dict
                ## revert to original validator
                for error in uniqueItemsValidator(validator, uI, instance, schema):
                    yield error
                return

        if non_unique_ids:
            yield ValidationError("Non-unique ID Values (first 3 shown):  {}".format(", ".join(list(non_unique_ids)[:3])))


validator.VALIDATORS.pop("patternProperties")
validator.VALIDATORS["uniqueItems"] = uniqueIds


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


def get_records_aggregates(json_data):
    # Unique ocids
    unique_ocids = set()

    if 'records' in json_data:
        for record in json_data['records']:
            # Gather all the ocids
            if 'ocid' in record:
                unique_ocids.add(record['ocid'])

    # Number of records
    count = len(json_data['records']) if 'records' in json_data else 0

    return {
        'count': count,
        'unique_ocids': unique_ocids,
    }


def get_grants_aggregates(json_data):
    
    id_count = 0
    count = 0
    unique_ids = set()
    duplicate_ids = set()
    max_award_date = ""
    min_award_date = ""
    max_amount_awarded = 0
    min_amount_awarded = 0
    distinct_funding_org_identifier = set()
    distinct_recipient_org_identifier = set()
    distinct_currency = set()

    if 'grants' in json_data:
        for grant in json_data['grants']:
            count = count + 1
            amountAwarded = grant.get('amountAwarded')
            if amountAwarded and isinstance(amountAwarded, (int, float)):
                max_amount_awarded = max(amountAwarded, max_amount_awarded)
                if not min_amount_awarded:
                    min_amount_awarded = amountAwarded
                min_amount_awarded = min(amountAwarded, min_amount_awarded)
            awardDate = str(grant.get('awardDate', ''))
            if awardDate:
                max_award_date = max(awardDate, max_award_date)
                if not min_award_date:
                    min_award_date = awardDate
                min_award_date = min(awardDate, min_award_date)
            grant_id = grant.get('id')
            if grant_id:
                id_count = id_count + 1
                if grant_id in unique_ids:
                    duplicate_ids.add(grant_id)
                unique_ids.add(grant_id)
            funding_orgs = grant.get('fundingOrganization', [])
            for funding_org in funding_orgs:
                funding_org_id = funding_org.get('id')
                if funding_org_id:
                    distinct_funding_org_identifier.add(funding_org_id)
            recipient_orgs = grant.get('recipientOrganization', [])
            for recipient_org in recipient_orgs:
                recipient_org_id = recipient_org.get('id')
                if recipient_org_id:
                    distinct_recipient_org_identifier.add(recipient_org_id)
            currency = grant.get('currency')
            if currency:
                distinct_currency.add(currency)

    return {
        'count': count,
        'id_count': id_count,
        'unique_ids': unique_ids,
        'duplicate_ids': duplicate_ids,
        'max_award_date': max_award_date,
        'min_award_date': min_award_date,
        'max_amount_awarded': max_amount_awarded,
        'min_amount_awarded': min_amount_awarded,
        'distinct_funding_org_identifier': distinct_funding_org_identifier,
        'distinct_recipient_org_identifier': distinct_recipient_org_identifier,
        'distinct_currency': distinct_currency
    }


def fields_present_generator(json_data, prefix=''):
    if not isinstance(json_data, dict):
        return
    for key, value in json_data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield from fields_present_generator(item, prefix + '/' + key)
            yield prefix + '/' + key
        elif isinstance(value, dict):
            yield from fields_present_generator(value, prefix + '/' + key)
            yield prefix + '/' + key
        else:
            # if a string value has an underscore in it, assume its a language property
            # and do not count as a present field.
            if '_' not in key:
                yield prefix + '/' + key


def get_fields_present(*args, **kwargs):
    counter = collections.Counter()
    counter.update(fields_present_generator(*args, **kwargs))
    return dict(counter)


def schema_dict_fields_generator(schema_dict):
    if 'properties' in schema_dict:
        for property_name, value in schema_dict['properties'].items():
            if 'oneOf' in value:
                property_schema_dicts = value['oneOf']
            else:
                property_schema_dicts = [value]
            for property_schema_dict in property_schema_dicts:
                property_type_set = get_property_type_set(property_schema_dict)
                if 'object' in property_type_set:
                    for field in schema_dict_fields_generator(property_schema_dict):
                        yield '/' + property_name + field
                elif 'array' in property_type_set:
                    fields = schema_dict_fields_generator(property_schema_dict['items'])
                    for field in fields:
                        yield '/' + property_name + field
                yield '/' + property_name


def get_schema_fields(schema_filename):
    r = requests.get(schema_filename)
    return set(schema_dict_fields_generator(jsonref.loads(r.text, object_pairs_hook=OrderedDict)))


def get_counts_additional_fields(schema_url, json_data):
    fields_present = get_fields_present(json_data)
    schema_fields = get_schema_fields(schema_url)
    data_only_all = set(fields_present) - schema_fields
    data_only = set()
    for field in data_only_all:
        parent_field = "/".join(field.split('/')[:-1])
        # only take fields with parent in schema (and top level fields)
        # to make results less verbose
        if not parent_field or parent_field in schema_fields:
            data_only.add(field)

    return [('/'.join(key.split('/')[:-1]), key.split('/')[-1], fields_present[key]) for key in data_only]


def datetime_or_date(instance):
    result = strict_rfc3339.validate_rfc3339(instance)
    if result:
        return result
    return datetime.datetime.strptime(instance, "%Y-%m-%d")


def get_schema_validation_errors(json_data, schema_url, current_app):
    schema = requests.get(schema_url).json()
    validation_errors = collections.defaultdict(list)
    format_checker = FormatChecker()
    if current_app == 'cove-360':
        format_checker.checkers['date-time'] = (datetime_or_date, ValueError)
    for n, e in enumerate(validator(schema, format_checker=format_checker).iter_errors(json_data)):
        validation_errors[e.message].append("/".join(str(item) for item in e.path))
    return dict(validation_errors)
    

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
    context = {}
    converted_path = os.path.join(data.upload_dir(), 'flattened')
    flatten_kwargs = dict(
        output_name=converted_path,
        main_sheet_name=request.cove_config['main_sheet_name'],
        root_list_path=request.cove_config['main_sheet_name'],
        root_id=request.cove_config['root_id'],
        schema=request.cove_config['item_schema_url'],
    )
    try:
        if not os.path.exists(converted_path + '.xlsx'):
            flattentool.flatten(data.original_file.file.name, **flatten_kwargs)
        context['converted_file_size'] = os.path.getsize(converted_path + '.xlsx')
        if request.cove_config['convert_titles']:
            flatten_kwargs.update(dict(
                output_name=converted_path + '-titles',
                use_titles=True
            ))
            if not os.path.exists(converted_path + '-titles.xlsx'):
                flattentool.flatten(data.original_file.file.name, **flatten_kwargs)
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


def convert_spreadsheet(request, data, file_type):
    context = {}
    converted_path = os.path.join(data.upload_dir(), 'unflattened.json')
    encoding = 'utf-8'
    if file_type == 'csv':
        # flatten-tool expects a directory full of CSVs with file names
        # matching what xlsx titles would be.
        # If only one upload file is specified, we rename it and move into
        # a new directory, such that it fits this pattern.
        input_name = os.path.join(data.upload_dir(), 'csv_dir')
        os.makedirs(input_name, exist_ok=True)
        destination = os.path.join(input_name, request.cove_config['main_sheet_name'] + '.csv')
        shutil.copy(data.original_file.file.name, destination)
        try:
            with open(destination, encoding='utf-8') as main_sheet_file:
                main_sheet_file.read()
        except UnicodeDecodeError:
            encoding = 'cp1252'
    else:
        input_name = data.original_file.file.name
    try:
        if not os.path.exists(converted_path):
            flattentool.unflatten(
                input_name,
                output_name=converted_path,
                input_format=file_type,
                main_sheet_name=request.cove_config['main_sheet_name'],
                root_id=request.cove_config['root_id'],
                schema=request.cove_config['item_schema_url'],
                convert_titles=True,
                encoding=encoding
            )
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
        'converted_url': '{}/unflattened.json'.format(data.upload_url())
    })
    return context


@CoveInputDataError.error_page
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
        "current_url": request.build_absolute_uri()
    }

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
                    'msg': _('We think you tried to upload a JSON file, but it is not well formed JSON.\n\nError message: {}'.format(err))
                })
        if request.current_app == 'cove-ocds' and 'records' in json_data:
            context['conversion'] = None
        else:
            context.update(convert_json(request, data))
    else:
        context.update(convert_spreadsheet(request, data, file_type))
        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp)

    schema_url = request.cove_config['schema_url']

    if request.current_app == 'cove-ocds':
        schema_url = schema_url['record'] if 'records' in json_data else schema_url['release']

    if schema_url:
        context.update({
            'data_only': sorted(get_counts_additional_fields(schema_url, json_data))
        })

    validation_errors_path = os.path.join(data.upload_dir(), 'validation_errors.json')
    if os.path.exists(validation_errors_path):
        with open(validation_errors_path) as validiation_error_fp:
            validation_errors = json.load(validiation_error_fp)
    else:
        validation_errors = get_schema_validation_errors(json_data, schema_url, request.current_app) if schema_url else None
        with open(validation_errors_path, 'w+') as validiation_error_fp:
            validiation_error_fp.write(json.dumps(validation_errors))

    context.update({
        'file_type': file_type,
        'schema_url': schema_url,
        'validation_errors': validation_errors,
        'json_data': json_data  # Pass the JSON data to the template so we can display values that need little processing
    })

    view = 'explore.html'
    if request.current_app == 'cove-ocds':
        if 'records' in json_data:
            context['records_aggregates'] = get_records_aggregates(json_data)
            view = 'explore_ocds-record.html'
        else:
            context['releases_aggregates'] = get_releases_aggregates(json_data)
            view = 'explore_ocds-release.html'
    elif request.current_app == 'cove-360':
        context['grants_aggregates'] = get_grants_aggregates(json_data)
        view = 'explore_360.html'

    return render(request, view, context)


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
