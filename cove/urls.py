from django.conf.urls import url
from django.views.generic import TemplateView


def cause500(request):
    raise Exception


urlpatterns = [
    url(r'^$', 'cove.input.views.input', name='index'),
    url(r'^data/(.+)$', 'cove.views.explore', name='explore'),
    url(r'^terms', TemplateView.as_view(template_name='terms.html'), name='terms'),
    url(r'^stats', 'cove.views.stats', name='stats'),
    url(r'^test/500', cause500),
]
