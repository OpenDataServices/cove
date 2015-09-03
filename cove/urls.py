from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^$', 'cove.input.views.input', name='index'),
    url(r'^data/(.+)$', 'cove.views.explore', name='explore'),
    url(r'^dataload/$', 'cove.dataload.views.dataload', name='dataload'),
    url(r'^dataload/(.+)$', 'cove.dataload.views.dataset', name='dataload_dataset'),
    url(r'^terms', TemplateView.as_view(template_name='terms.html'), name='terms'),
    url(r'^stats', 'cove.views.stats', name='stats'),
]
