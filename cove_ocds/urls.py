from django.conf.urls import url, include
from django.views.generic import RedirectView

from cove.urls import urlpatterns, handler500  # noqa: F401

urlpatterns += [url(r'^data/(.+)$', 'cove_ocds.views.explore_ocds', name='explore')]

# Serve the OCDS validator at /validator/
urlpatterns = [
    url(r'^$', RedirectView.as_view(url='validator/', permanent=False)),
    url('^validator/', include(urlpatterns))
]
