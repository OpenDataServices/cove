import logging
import json
import tempfile
import os
import functools

from django.shortcuts import render
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest

from libcove.lib.exceptions import CoveInputDataError
from libcove.lib.converters import convert_spreadsheet, convert_json
from libcove.config import LibCoveConfig
from cove.input.models import SuppliedData
from cove.input.views import data_input
from cove.views import explore_data_context
from .lib.iati import common_checks_context_iati, get_file_type
from .lib.process_codelists import aggregate_results
from .lib.api import iati_json_output
from .lib.schema import SchemaIATI
from django.conf import settings


logger = logging.getLogger(__name__)


def cove_web_input_error(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except CoveInputDataError as err:
            return render(request, 'error.html', context=err.context)
    return wrapper


class UploadForm(forms.ModelForm):
    class Meta:
        model = SuppliedData
        fields = ['original_file']
        labels = {
            'original_file': _('Upload a file (.csv, .xlsx, .xml)')
        }


class UrlForm(forms.ModelForm):
    class Meta:
        model = SuppliedData
        fields = ['source_url']
        labels = {
            'source_url': _('Supply a URL')
        }


class TextForm(forms.Form):
    paste = forms.CharField(label=_('Paste (XML only)'), widget=forms.Textarea)


class UploadApi(forms.Form):
    name = forms.CharField(max_length=200)
    file = forms.FileField()
    openag = forms.BooleanField(required=False)
    orgids = forms.BooleanField(required=False)


iati_form_classes = {
    'upload_form': UploadForm,
    'url_form': UrlForm,
    'text_form': TextForm,
}


def data_input_iati(request):
    return data_input(request, form_classes=iati_form_classes, text_file_name='text.xml')


@cove_web_input_error
def explore_iati(request, pk):
    context, db_data, error = explore_data_context(request, pk, get_file_type)
    if error:
        return error

    lib_cove_config = LibCoveConfig()
    lib_cove_config.config.update(settings.COVE_CONFIG)

    file_type = context['file_type']
    if file_type != 'xml':
        schema_iati = SchemaIATI()
        context.update(convert_spreadsheet(
            db_data.upload_dir(), db_data.upload_url(), db_data.original_file.file.name,
            file_type, lib_cove_config, xml=True,
            xml_schemas=[
                schema_iati.activity_schema,
                schema_iati.organisation_schema,
                schema_iati.common_schema,
            ]))
        data_file = context['converted_path']
    else:
        data_file = db_data.original_file.file.name
        context.update(convert_json(db_data.upload_dir(), db_data.upload_url(), db_data.original_file.file.name,
                       request=request, flatten=request.POST.get('flatten'), xml=True, lib_cove_config=lib_cove_config))

    context = common_checks_context_iati(context, db_data.upload_dir(), data_file, file_type)
    context['first_render'] = not db_data.rendered
    context['invalid_embedded_codelist_values'] = aggregate_results(context['invalid_embedded_codelist_values'])

    if not db_data.rendered:
        db_data.rendered = True

    return render(request, 'cove_iati/explore.html', context)


@require_POST
@csrf_exempt
def api_test(request):
    form = UploadApi(request.POST, request.FILES)
    if form.is_valid():
        with tempfile.TemporaryDirectory() as tmpdirname:
            file_path = os.path.join(tmpdirname, form.cleaned_data['name'])
            with open(file_path, 'wb+') as destination:
                for chunk in request.FILES['file'].chunks():
                    destination.write(chunk)
            result = iati_json_output(tmpdirname, file_path, form.cleaned_data['openag'], form.cleaned_data['orgids'])
            return HttpResponse(json.dumps(result), content_type='application/json')
    else:
        return HttpResponseBadRequest(json.dumps(form.errors), content_type='application/json')
