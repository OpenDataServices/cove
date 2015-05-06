from django.conf.urls import url

urlpatterns = [
    url(r'^$', 'cove.input.views.input', name='index'),
    url(r'^data/(.+)$', 'cove.views.explore', name='explore'),
]
