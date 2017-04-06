from django.conf.urls import url

from cove.urls import urlpatterns
from django.conf.urls.static import static
from django.conf import settings


urlpatterns += [url(r'^data/(.+)$', 'cove_iati.views.explore_iati', name='explore')]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
