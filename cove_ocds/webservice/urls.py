from django.conf.urls import url

from cove.urls import urlpatterns as urlpatterns_core
import cove_ocds.webservice.views

urlpatterns_core += [url(r'^raw/(.+)$', cove_ocds.webservice.views.explore_ocds_raw, name='explore_raw')]