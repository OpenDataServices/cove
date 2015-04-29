from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from cove.input.models import SuppliedData
from django.conf import settings
import os
import shutil
import json
import flattentool
import magic


def get_releases_aggregates(json_data):
    return {
        'count': len(json_data['releases']) if 'releases' in json_data else 0
    }


class UnrecognisedFileType(Exception):
    pass


def get_file_type(django_file):
    buf = django_file.read(1024)
    type_name = magic.from_buffer(buf).decode('utf8')
    mime_type = magic.from_buffer(buf, mime=True).decode('utf8')
    if mime_type == 'text/plain':
        return 'json'
    elif type_name in ['Microsoft OOXML', 'Microsoft Excel 2007+']:
        return 'xlsx'
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
        flattentool.flatten(
            original_file.file.name,
            output_name=converted_path,
            main_sheet_name='releases'
        )
        json_path = original_file.file.name
    else:
        converted_path = os.path.join(converted_dir, 'unflattened.json')
        converted_url = '{}converted/{}/unflattened.json'.format(settings.MEDIA_URL, pk)
        conversion = 'unflatten'
        flattentool.unflatten(
            original_file.file.name,
            output_name=converted_path,
            input_format=file_type,
            main_sheet_name='releases'
        )
        json_path = converted_path

    with open(json_path) as fp:
        json_data = json.load(fp)
        releases_aggregates = get_releases_aggregates(json_data)

    return render(request, 'explore.html', {
        'conversion': conversion,
        'original_file': original_file,
        'converted_url': converted_url,
        'file_type': file_type,
        'releases_aggregates': releases_aggregates
    })
