from django.conf.urls import url

from cove.urls import urlpatterns, handler500  # noqa: F401


urlpatterns += [
    url(r'^data/(.+)$', 'cove_360.views.explore_360', name='explore'),
    url(r'^common_errors', 'cove_360.views.common_errors', name='common_errors')
]
