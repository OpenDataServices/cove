from django.conf.urls import url

from cove.urls import urlpatterns, handler500  # noqa: F401


urlpatterns = [
    url(r'^$', 'cove_iati.views.input_iati', name='index'),
    url(r'^data/(.+)$', 'cove_iati.views.explore_iati', name='explore'),
] + urlpatterns
