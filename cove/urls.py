from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView

from django.template import loader
from django.http import HttpResponseServerError

import cove.input.views
import cove.views


def handler500(request):
    """500 error handler which includes ``request`` in the context.
    """

    context = {
        'request': request,
    }
    context.update(settings.COVE_CONFIG)

    t = loader.get_template('500.html')
    return HttpResponseServerError(t.render(context))


def cause500(request):
    raise Exception


urlpatterns = [
    url(r'^$', cove.input.views.data_input, name='index'),
    url(r'^terms', TemplateView.as_view(template_name='terms.html'), name='terms'),
    url(r'^stats', cove.views.stats, name='stats'),
    url(r'^test/500', cause500),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n'))
]
