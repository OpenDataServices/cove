from django.conf.urls import url

from cove import urlpatterns

urlpatterns += [url(r'^data/(.+)$', 'cove360.views.explore', name='explore')]
