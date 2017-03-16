from django.conf.urls import url

from cove.urls import urlpatterns


urlpatterns += [url(r'^data/(.+)$', 'cove-ocds.views.explore_ocds', name='explore')]
