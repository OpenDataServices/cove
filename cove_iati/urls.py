from django.conf.urls import url

from cove import urlpatterns


urlpatterns += [url(r'^data/(.+)$', 'cove_iati.views.explore_iati', name='explore')]
