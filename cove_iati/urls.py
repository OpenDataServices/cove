from django.urls import re_path

from cove.urls import urlpatterns, handler500  # noqa: F401
from django.conf.urls.static import static
from django.conf import settings

import cove_iati.views

urlpatterns = [
    re_path(r'^$', cove_iati.views.data_input_iati, name='index'),
    re_path(r'^data/(.+)/(.+)$', cove_iati.views.explore_iati, name='explore_suffix'),
    re_path(r'^data/(.+)$', cove_iati.views.explore_iati, name='explore'),
    re_path(r'^api_test', cove_iati.views.api_test, name='api_test'),
] + urlpatterns

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
