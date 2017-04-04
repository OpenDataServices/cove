from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings

from cove.urls import urlpatterns, handler500  # noqa: F401


urlpatterns += [
    url(r'^data/(.+)$', 'cove_360.views.explore_360', name='explore'),
    url(r'^common_errors', 'cove_360.views.common_errors', name='common_errors')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
