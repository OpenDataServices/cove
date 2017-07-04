from django.conf import settings


def analytics(request):
    return {
        'piwik': settings.PIWIK,
        'google_analytics_id': settings.GOOGLE_ANALYTICS_ID
    }


def input_methods(request):
    return {'input_methods': settings.COVE_CONFIG.get('input_methods', []),
            'app_verbose_name': settings.COVE_CONFIG.get('app_verbose_name', [])}
