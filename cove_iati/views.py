import json
import logging
import os

from django.shortcuts import render
from django import forms
from django.utils.translation import ugettext_lazy as _
import defusedxml.lxml as etree
import lxml.etree

from .lib.schema import SchemaIATI
from .lib.iati import format_lxml_errors, get_xml_validation_errors, lxml_errors_generator
from .lib.iati_utils import sort_iati_xml_file
from cove.lib.converters import convert_spreadsheet
from cove.lib.exceptions import CoveInputDataError, cove_web_input_error
from cove.input.models import SuppliedData
from cove.input.views import data_input
from cove.views import explore_data_context


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


def common_checks_context_iati(db_data, data_file, file_type):
    schema_aiti = SchemaIATI()
    lxml_errors = {}
    cell_source_map = {}
    validation_errors_path = os.path.join(db_data.upload_dir(), 'validation_errors-2.json')

    with open(data_file) as fp, open(schema_aiti.activity_schema) as schema_fp:
        try:
            tree = etree.parse(fp)
        except lxml.etree.XMLSyntaxError as err:
            raise CoveInputDataError(context={
                'sub_title': _("Sorry we can't process that data"),
                'link': 'index',
                'link_text': _('Try Again'),
                'msg': _('We think you tried to upload a XML file, but it is not well formed XML.'
                         '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                         '</span> <strong>Error message:</strong> {}'.format(err)),
                'error': format(err)
            })
        schema_tree = etree.parse(schema_fp)
        schema = lxml.etree.XMLSchema(schema_tree)
        schema.validate(tree)
        lxml_errors = lxml_errors_generator(schema.error_log)

    errors_all = format_lxml_errors(lxml_errors)

    if file_type != 'xml':
        with open(os.path.join(db_data.upload_dir(), 'cell_source_map.json')) as cell_source_map_fp:
            cell_source_map = json.load(cell_source_map_fp)

    if os.path.exists(validation_errors_path):
        with open(validation_errors_path) as validation_error_fp:
            validation_errors = json.load(validation_error_fp)
    else:
        validation_errors = get_xml_validation_errors(errors_all, file_type, cell_source_map)

        with open(validation_errors_path, 'w+') as validation_error_fp:
            validation_error_fp.write(json.dumps(validation_errors))

    db_data.rendered = True

    return {
        'validation_errors': sorted(validation_errors.items()),
        'validation_errors_count': sum(len(value) for value in validation_errors.values()),
        'cell_source_map': cell_source_map,
        'first_render': False
    }


def data_input_iati(request):
    return data_input(request, form_classes=iati_form_classes, text_file_name='text.xml')


@cove_web_input_error
def explore_iati(request, pk):
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error

    file_type = context['file_type']
    if file_type != 'xml':
        context.update(convert_spreadsheet(request, db_data, file_type, xml=True))
        data_file = context['converted_path']
        # sort converted xml
        sort_iati_xml_file(context['converted_path'], context['converted_path'])
    else:
        data_file = db_data.original_file.file.name

    context.update(common_checks_context_iati(db_data, data_file, file_type))
    return render(request, 'cove_iati/explore.html', context)
