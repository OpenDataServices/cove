import logging
from datetime import timedelta

from django.db.models.aggregates import Count
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from cove.input.models import SuppliedData
from cove.lib.tools import get_file_type

logger = logging.getLogger(__name__)


def explore_data_context(request, pk):
    try:
        data = SuppliedData.objects.get(pk=pk)
    except (SuppliedData.DoesNotExist, ValidationError):  # Catches primary key does not exist and badly formed UUID
        return {}, None, render(request, 'error.html', {
            'sub_title': _('Sorry, the page you are looking for is not available'),
            'link': 'index',
            'link_text': _('Go to Home page'),
            'msg': _("We don't seem to be able to find the data you requested.")
            }, status=404)

    try:
        data.original_file.file.name
    except FileNotFoundError:
        return {}, None, render(request, 'error.html', {
            'sub_title': _('Sorry, the page you are looking for is not available'),
            'link': 'index',
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

    return (context, data, None)


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
