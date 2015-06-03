from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from cove.input.models import SuppliedData
from django.conf import settings
import os
import shutil
import json
import flattentool
from flattentool.json_input import BadlyFormedJSONError
import requests
from jsonschema.validators import Draft4Validator as validator


def get_releases_aggregates(json_data):
    # Unique ocids & Release dates
    ocids = []
    unique_ocids = []
    release_dates = []
    earliest_release_date = None
    latest_release_date = None
    table_data = {}
    if 'releases' in json_data:
        for release in json_data['releases']:
            # Gather all the ocids
            ocids.append(release['ocid']) if 'ocid' in release else 0
            
            #Gather all the release dates
            release_dates.append(release['date']) if 'date' in release else 0
            
            # Some identifying data from a release that could be displayed in a table
            generic_info = {}
            if 'tender' in release:
                if 'items' in release['tender']:
                    if 'description' in release['tender']['items']:
                        generic_info['description'] = release['tender']['items'][0]['description']
            if 'buyer' in release:
                if 'name' in release['buyer']:
                    generic_info['buyer'] = release['buyer']['name']
            if 'ocid' in release:
                table_data[release['ocid']] = generic_info
        
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
        'table_data': table_data
    }


def get_grants_aggregates(json_data):
    count = len(json_data['grants']) if 'grants' in json_data else 0
    
    return {
        'count': count,
    }


def get_schema_validation_errors(json_data, schema_url):
    schema = requests.get(schema_url).json()
    validation_error_list = []
    for n, e in enumerate(validator(schema).iter_errors(json_data)):
        if n >= 100:
            break
        validation_error_list.append(e)
    return validation_error_list
    

class UnrecognisedFileType(Exception):
    pass


def get_file_type(django_file):
    if django_file.name.endswith('.json'):
        return 'json'
    elif django_file.name.endswith('.xlsx'):
        return 'xlsx'
    else:
        first_byte = django_file.read(1)
        if first_byte in [b'{', b'[']:
            return 'json'
        else:
            raise UnrecognisedFileType


def explore(request, pk):
    data = SuppliedData.objects.get(pk=pk)
    original_file = data.original_file

    converted_dir = os.path.join(settings.MEDIA_ROOT, 'converted', pk)
    try:
        shutil.rmtree(converted_dir)
    except FileNotFoundError:
        pass
    os.makedirs(converted_dir)
    
    try:
        file_type = get_file_type(original_file)
    except UnrecognisedFileType:
        return render(request, 'error.html', {
            'msg': _('Unrecognised file type.')
        })
    if file_type == 'json':
        converted_path = os.path.join(converted_dir, 'flattened')
        converted_url = '{}converted/{}/flattened'.format(settings.MEDIA_URL, pk)
        conversion = 'flatten'
        try:
            flattentool.flatten(
                original_file.file.name,
                output_name=converted_path,
                main_sheet_name=request.cove_config['main_sheet_name'],
                root_list_path=request.cove_config['main_sheet_name'],
                root_id=request.cove_config['root_id'],
            )
        except BadlyFormedJSONError as err:
            return render(request, 'error.html', {
                'msg': _('We think you tried to upload a JSON file, but it is not well formed JSON.\n\nError message: {}'.format(err))
            })
        json_path = original_file.file.name
    else:
        converted_path = os.path.join(converted_dir, 'unflattened.json')
        converted_url = '{}converted/{}/unflattened.json'.format(settings.MEDIA_URL, pk)
        conversion = 'unflatten'
        flattentool.unflatten(
            original_file.file.name,
            output_name=converted_path,
            input_format=file_type,
            main_sheet_name=request.cove_config['main_sheet_name'],
            root_id=request.cove_config['root_id'],
        )
        json_path = converted_path

    with open(json_path) as fp:
        json_data = json.load(fp)
        schema_url = request.cove_config['schema_url']

        context = {
            'conversion': conversion,
            'original_file': original_file,
            'converted_url': converted_url,
            'file_type': file_type,
            'schema_url': schema_url,
            'validation_error_list': get_schema_validation_errors(json_data, schema_url) if schema_url else None
        }

        if request.current_app == 'cove-ocds':
            context['releases_aggregates'] = get_releases_aggregates(json_data)
        elif request.current_app == 'cove-360':
            context['grants_aggregates'] = get_grants_aggregates(json_data)

        return render(request, 'explore.html', context)
