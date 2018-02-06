from django.conf.urls import url, include
from django.views.generic import RedirectView, TemplateView
from django.conf.urls.static import static
from django.conf import settings

from cove.urls import urlpatterns as urlpatterns_core
from cove.urls import handler500  # noqa: F401

import cove_ocds.views


# Serve the OCDS validator at /validator/
urlpatterns_core += [url(r'^data/(.+)$', cove_ocds.views.explore_ocds, name='explore')]

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='validator/', permanent=False)),
    url('^validator/', include(urlpatterns_core)),
    url(r'^validator/terms_ocds$', TemplateView.as_view(template_name='terms_ocds.html'), name='terms'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
