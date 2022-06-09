from django.conf.urls import url

from cove.urls import urlpatterns, handler500  # noqa: F401
from django.conf.urls.static import static
from django.conf import settings

import cove_iati.views

urlpatterns = [
    url(r'^$', cove_iati.views.data_input_iati, name='index'),
    url(r'^data/(.+)/(.+)$', cove_iati.views.explore_iati, name='explore_suffix'),
    url(r'^data/(.+)$', cove_iati.views.explore_iati, name='explore'),
    url(r'^api_test', cove_iati.views.api_test, name='api_test'),
] + urlpatterns

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
