from django.conf import settings


def piwik(request):
    return {'piwik': settings.PIWIK}
