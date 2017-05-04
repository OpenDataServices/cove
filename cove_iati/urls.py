from django.conf.urls import url

from cove.urls import urlpatterns, handler500  # noqa: F401
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    url(r'^$', 'cove_iati.views.data_input_iati', name='index'),
    url(r'^data/(.+)$', 'cove_iati.views.explore_iati', name='explore'),
] + urlpatterns

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
