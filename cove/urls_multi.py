
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^ocds/', include('cove.urls', namespace='cove-ocds', app_name='cove')),
    url(r'^360/', include('cove.urls', namespace='cove-360', app_name='cove')),
    url(r'^resourceprojects/', include('cove.urls', namespace='cove-resourceprojects', app_name='cove')),
    url(r'^$', TemplateView.as_view(template_name='multi_index.html'), name='multi_index'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
