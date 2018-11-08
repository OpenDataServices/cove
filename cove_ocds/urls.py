from django.conf.urls import url, include
from django.views.generic import RedirectView
from django.conf.urls.static import static
from django.conf import settings

from cove.urls import urlpatterns as urlpatterns_core
from cove.urls import handler500  # noqa: F401

import cove_ocds.views


# Serve the OCDS validator at /validator/
urlpatterns_core += [url(r'^data/(.+)$', cove_ocds.views.explore_ocds, name='explore')]

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='review/', permanent=False)),
    # This is the old URL's.
    url('^validator/', include(urlpatterns_core)),
    # This is the new URL's. This is last in order so that it is more important.
    # When the user submits some data, they will be redirected to a page with a /review URL.
    url('^review/', include(urlpatterns_core)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
