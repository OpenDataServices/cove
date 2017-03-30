import logging

from django.shortcuts import render
from django import forms
from django.utils.translation import ugettext_lazy as _

from cove.lib.converters import convert_spreadsheet
from cove.lib.exceptions import CoveWebInputDataError
from cove.views import explore_data_context

from cove.input.models import SuppliedData
from cove.input.views import input

logger = logging.getLogger(__name__)


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


iati_form_classes = {
    'upload_form': UploadForm,
    'url_form': UrlForm,
    'text_form': TextForm,
}


def common_checks_iati(context, db_data, json_data, schema_obj):
    return context


def input_iati(request):
    return input(request, form_classes=iati_form_classes, text_file_name='text.xml')


@CoveWebInputDataError.error_page
def explore_iati(request, pk):
    #schema_360 = Schema360()
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error
    file_type = context['file_type']
    if file_type != 'xml':
        # open the data first so we can inspect for record package
        context.update(convert_spreadsheet(request, db_data, file_type, xml=True))
        #with open(context['converted_path'], encoding='utf-8') as fp:
        #    json_data = json.load(fp)

    return render(request, 'cove_iati/explore.html', context)
