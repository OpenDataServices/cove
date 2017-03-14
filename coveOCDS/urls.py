from django.conf.urls import url

from cove import urlpatterns


urlpatterns += [url(r'^data/(.+)$', 'coveOCDS.views.explore', name='explore')]
