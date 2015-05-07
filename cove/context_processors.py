from django.conf import settings


def piwik(request):
    return {'piwik': settings.PIWIK}


def cove_namespace_context(request):
    return request.cove_config
