from django.conf.urls import url

from cove.urls import urlpatterns, handler500  # noqa: F401


urlpatterns += [url(r'^data/(.+)$', 'cove_ocds.views.explore_ocds', name='explore')]
