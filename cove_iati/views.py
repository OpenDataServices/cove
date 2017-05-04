import logging

from django.shortcuts import render
from django import forms
from django.utils.translation import ugettext_lazy as _
from lxml import etree

from cove.lib.converters import convert_spreadsheet
from cove.lib.exceptions import cove_web_input_error
from cove.input.models import SuppliedData
from cove.input.views import UrlForm, data_input
from cove.views import explore_data_context

logger = logging.getLogger(__name__)


class UploadForm(forms.ModelForm):
    class Meta:
        model = SuppliedData
        fields = ['original_file']
        labels = {
            'original_file': _('Upload a file (.csv, .xlsx, .xml)')
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


def data_input_iati(request):
    return data_input(request, form_classes=iati_form_classes, text_file_name='text.xml')


@cove_web_input_error
def explore_iati(request, pk):
    #schema_360 = Schema360()
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error
    file_type = context['file_type']
    if file_type != 'xml':
        context.update(convert_spreadsheet(request, db_data, file_type, xml=True))

        with open(context['converted_path']) as fp, open('IATI-Schemas/iati-activities-schema.xsd') as schema_fp:
            tree = etree.parse(fp)
            schema_tree = etree.parse(schema_fp)
            schema = etree.XMLSchema(schema_tree)
            schema.validate(tree)
            for error in schema.error_log:
                print(error)
                print(error.path)

    return render(request, 'cove_iati/explore.html', context)
