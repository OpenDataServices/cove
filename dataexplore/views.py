from django.shortcuts import render
from datainput.models import SuppliedData
from django.conf import settings
import os
import shutil
import json
import flattentool

def explore(request, pk):
    data = SuppliedData.objects.get(pk=pk)
    # Assume JSON for now
    converted_dir = os.path.join(settings.MEDIA_ROOT, 'converted', pk) 
    try:
        shutil.rmtree(converted_dir)
    except FileNotFoundError:
        pass
    os.makedirs(converted_dir)
    converted_path = os.path.join(converted_dir, 'flattened')
    flattentool.flatten(
        data.original_file.file.name,
        output_name=converted_path,
    )
    return render(request, 'explore.html', {
        'converted_url': '{}converted/{}/flattened'.format(settings.MEDIA_URL, pk)
    })
