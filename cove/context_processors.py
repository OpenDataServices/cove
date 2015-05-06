from django.conf import settings
from django.utils.translation import ugettext_lazy as _


def piwik(request):
    return {'piwik': settings.PIWIK}


def namespace_context(request):
    namespace = request.resolver_match.namespace
    request.current_app = namespace

    by_namespace = {
        'base_template_name': {
            'cove-ocds': 'base_ocds.html',
            'cove-360': 'base_360.html',
            'default': 'base_generic.html',
        },
        'application_name': {
            'cove-ocds': _('Open Contracting Data Tool'),
            'cove-360': _('360 Giving Data Tool'),
            'default': _('Cove'),
        },
    }
    return {key: by_namespace[key][namespace] if namespace in by_namespace[key] else by_namespace[key]['default'] for key in by_namespace}
