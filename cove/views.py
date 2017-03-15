import json
import logging
import os
from datetime import timedelta

from django.db.models.aggregates import Count
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

import cove.lib.common as common
from cove.input.models import SuppliedData
from cove.lib.tools import get_file_type

logger = logging.getLogger(__name__)


def explore_data_context(request, pk):
    try:
        data = SuppliedData.objects.get(pk=pk)
    except (SuppliedData.DoesNotExist, ValueError):  # Catches: Primary key does not exist, and badly formed hexadecimal UUID string
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
            'msg': _('The data you were hoping to explore no longer exists.\n\nThis is because all '
                     'data suplied to this website is automatically deleted after 7 days, and therefore '
                     'the analysis of that data is no longer available.')
        }, status=404)

    file_type = get_file_type(data.original_file)
    context = {
        'original_file': {
            'url': data.original_file.url,
            'size': data.original_file.size
        },
        'file_type': file_type,
        'data_uuid': pk,
        'current_url': request.build_absolute_uri(),
        'source_url': data.source_url,
        'form_name': data.form_name,
        'created_datetime': data.created.strftime('%A, %d %B %Y %I:%M%p %Z'),
        'created_date': data.created.strftime('%A, %d %B %Y'),
    }

    return (context, data)


def common_checks_context(request, data, json_data, schema_obj, schema_name, context):
    # schema_name = schema_obj.release_pkg_schema_name
    # if 'records' in json_data:
    #     schema_name = schema_obj.record_pkg_schema_name

    schema_version = getattr(schema_obj, 'version', None)
    schema_version_choices = getattr(schema_obj, 'version_choices', None)
    if schema_version:
        schema_version_display_choices = tuple(
            (version, display_url[0]) for version, display_url in schema_version_choices.items()
        )
        context.update({
            'version_used': schema_version,
            'version_display_choices': schema_version_display_choices,
            'version_used_display': schema_version_choices[schema_version][0]}
        )

    additional_fields = sorted(common.get_counts_additional_fields(json_data, schema_obj, schema_name,
                                                                   context, request.current_app))
    context.update({
        'data_only': additional_fields,
        'additional_fields_count': sum(item[2] for item in additional_fields)
    })

    cell_source_map = {}
    heading_source_map = {}
    if context['file_type'] != 'json':  # Assume it is csv or xlsx
        with open(os.path.join(data.upload_dir(), 'cell_source_map.json')) as cell_source_map_fp:
            cell_source_map = json.load(cell_source_map_fp)

        with open(os.path.join(data.upload_dir(), 'heading_source_map.json')) as heading_source_map_fp:
            heading_source_map = json.load(heading_source_map_fp)

    validation_errors_path = os.path.join(data.upload_dir(), 'validation_errors-2.json')
    if os.path.exists(validation_errors_path):
        with open(validation_errors_path) as validiation_error_fp:
            validation_errors = json.load(validiation_error_fp)
    else:
        validation_errors = common.get_schema_validation_errors(json_data, schema_obj, schema_name,
                                                                request.current_app, cell_source_map,
                                                                heading_source_map)
        with open(validation_errors_path, 'w+') as validiation_error_fp:
            validiation_error_fp.write(json.dumps(validation_errors))

    extensions = None
    if getattr(schema_obj, 'extensions', None):
        extensions = {
            'extensions': schema_obj.extensions,
            'invalid_extension': schema_obj.invalid_extension,
            'is_extended_schema': schema_obj.extended,
            'extended_schema_url': schema_obj.extended_schema_url
        }

    context.update({
        'schema_url': schema_obj.release_pkg_schema_url,
        'extensions': extensions,
        'validation_errors': sorted(validation_errors.items()),
        'validation_errors_count': sum(len(value) for value in validation_errors.values()),
        'deprecated_fields': common.get_json_data_deprecated_fields(json_data, schema_obj),
        'json_data': json_data,  # Pass the JSON data to the template so we can display values that need little processing
        'first_render': not data.rendered,
        'common_error_types': []
    })

    if not data.rendered:
        data.rendered = True
    if schema_version:
        data.schema_version = schema_version
    data.save()

    return {
        'context': context,
        'cell_source_map': cell_source_map,
    }


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
