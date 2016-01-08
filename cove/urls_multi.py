
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

if settings.PREFIX_MAP:
    urls = []
    prefix_ocds = settings.PREFIX_MAP.get('ocds')
    if prefix_ocds is not None:
        urls.append(url(prefix_ocds, include('cove.urls', namespace='cove-ocds', app_name='cove')))
    prefix_360 = settings.PREFIX_MAP.get('360')
    if prefix_360 is not None:
        urls.append(url(prefix_360, include('cove.urls', namespace='cove-360', app_name='cove')))
else:
    urls = [
        url(r'^ocds/', include('cove.urls', namespace='cove-ocds', app_name='cove')),
        url(r'^360/', include('cove.urls', namespace='cove-360', app_name='cove')),
        url(r'^$', TemplateView.as_view(template_name='multi_index.html'), name='multi_index'),
    ]

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
] + urls + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
