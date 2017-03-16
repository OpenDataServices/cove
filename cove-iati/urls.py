from django.conf.urls import url

from cove import urlpatterns


urlpatterns += [url(r'^data/(.+)$', 'cove-iati.views.explore_iati', name='explore')]
