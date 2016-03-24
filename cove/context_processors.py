from django.conf import settings


def analytics(request):
    return {
        'piwik': settings.PIWIK,
        'google_analytics_id': settings.GOOGLE_ANALYTICS_ID
    }


def cove_namespace_context(request):
    return request.cove_config
