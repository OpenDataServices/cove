from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from datainput.models import SuppliedData
from django.conf import settings
import os
import shutil
import json
import flattentool
import magic

def explore(request, pk):
    data = SuppliedData.objects.get(pk=pk)
    original_file = data.original_file

    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(original_file.file.name)

    converted_dir = os.path.join(settings.MEDIA_ROOT, 'converted', pk) 
    try:
        shutil.rmtree(converted_dir)
    except FileNotFoundError:
        pass
    os.makedirs(converted_dir)
    
    if mime_type == b'text/plain':
        converted_path = os.path.join(converted_dir, 'flattened')
        converted_url = '{}converted/{}/flattened'.format(settings.MEDIA_URL, pk)
        conversion = 'flatten'
        flattentool.flatten(
            original_file.file.name,
            output_name=converted_path,
            main_sheet_name='releases'
        )
    elif mime_type == b'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        converted_path = os.path.join(converted_dir, 'unflattened.json')
        converted_url = '{}converted/{}/unflattened.json'.format(settings.MEDIA_URL, pk)
        conversion = 'unflatten'
        flattentool.unflatten(
            original_file.file.name,
            output_name=converted_path,
            input_format='xlsx',
            main_sheet_name='releases'
        )
    else:
        return render(request, 'error.html', {
            'msg': _('Unrecognised file type.'),
        })


    return render(request, 'explore.html', {
        'conversion': conversion,
        'original_file': original_file,
        'converted_url': converted_url,
        'mime_type': mime_type,
    })
