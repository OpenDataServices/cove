DJANGO_SETTINGS_MODULE=cove.settings py.test cove --cov --cov-report= $@
DJANGO_SETTINGS_MODULE=cove_iati.settings py.test cove_iati --cov-append --cov $@
