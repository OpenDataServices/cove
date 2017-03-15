from django.conf.urls import url

from cove import urlpatterns


urlpatterns += [url(r'^data/(.+)$', 'coveIATI.views.explore', name='explore')]
