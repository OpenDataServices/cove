from django.conf.urls import url

from cove.urls import urlpatterns


urlpatterns += [url(r'^data/(.+)$', 'cove_ocds.views.explore_ocds', name='explore')]
