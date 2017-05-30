import json
import logging
import os
import re

from django.shortcuts import render
from django import forms
from django.utils.translation import ugettext_lazy as _
from lxml import etree

from .lib.schema import SchemaIATI
from cove.lib.converters import convert_spreadsheet
from cove.lib.exceptions import cove_web_input_error
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
    validation_errors = {}

    with open(data_file) as fp, open(schema_aiti.activity_schema) as schema_fp:
        tree = etree.parse(fp)
        schema_tree = etree.parse(schema_fp)
        schema = etree.XMLSchema(schema_tree)
        schema.validate(tree)

        for error in schema.error_log:
            lxml_errors[error.path] = error.message

        # lxml uses path indexes starting from 1
        errors_all = {}
        for error_path, error_message in lxml_errors.items():
            indexes = ['/{}'.format(str(int(i[1:-1]) - 1)) for i in re.findall(r'\[\d+\]', error_path)]
            path = re.sub(r'\[\d+\]', '{}', error_path).format(*indexes)
            path = re.sub(r'/iati-activities/', '', path)
            errors_all[path] = error_message.replace('Element ', '')

    if file_type != 'xml':
        with open(os.path.join(db_data.upload_dir(), 'cell_source_map.json')) as cell_source_map_fp:
            cell_source_map = json.load(cell_source_map_fp)

    validation_errors_path = os.path.join(db_data.upload_dir(), 'validation_errors-2.json')

    if os.path.exists(validation_errors_path):
        with open(validation_errors_path) as validation_error_fp:
            validation_errors = json.load(validation_error_fp)
    else:
        cell_source_map_paths = cell_source_map.keys()
        for error_path, error_message in errors_all.items():
            validation_key = json.dumps(['', error_message])
            validation_errors[validation_key] = []
            for cell_path in cell_source_map_paths:
                if len(validation_errors[validation_key]) == 3:
                    break
                if error_path in cell_path:
                    if len(cell_source_map[cell_path][0]) > 2:
                        sources = {
                            'sheet': cell_source_map[cell_path][0][0],
                            "col_alpha": cell_source_map[cell_path][0][1],
                            'row_number': cell_source_map[cell_path][0][2],
                            'header': cell_source_map[cell_path][0][3],
                            'path': cell_path
                        }
                        if sources not in validation_errors[validation_key]:
                            validation_errors[validation_key].append(sources)

        with open(validation_errors_path, 'w+') as validation_error_fp:
            validation_error_fp.write(json.dumps(validation_errors))

    db_data.rendered = True

    return {
        'validation_errors': sorted(validation_errors.items()),
        'validation_errors_count': sum(len(value) for value in validation_errors.values()),
        'cell_source_map': cell_source_map,
        'first_render': not db_data.rendered,
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
    else:
        data_file = db_data.original_file.file.name

    context.update(common_checks_context_iati(db_data, data_file, file_type))
    return render(request, 'cove_iati/explore.html', context)
