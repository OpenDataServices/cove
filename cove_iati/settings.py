import sys
import os
import environ
if "pytest" not in sys.modules:
    # Check that we can import defusedexpat, as this will protect us against
    # some XML attacks in xmltodict
    # Needs a noqa comment as we don't actually use it here
    import defusedexpat  # noqa: F401
    pass

# Needs a noqa comment to come after the above import
from cove import settings  # noqa: E408


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(  # set default values and casting
    DB_NAME=(str, os.path.join(BASE_DIR, 'db.sqlite3')),
)

PIWIK = settings.PIWIK
GOOGLE_ANALYTICS_ID = settings.GOOGLE_ANALYTICS_ID

# We can't take MEDIA_ROOT and MEDIA_URL from cove settings,
# ... otherwise the files appear under the BASE_DIR that is the Cove library install.
# That could get messy. We want them to appear in our directory.
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

DEALER_TYPE = settings.DEALER_TYPE
SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.DEBUG
ALLOWED_HOSTS = settings.ALLOWED_HOSTS
MIDDLEWARE_CLASSES = settings.MIDDLEWARE_CLASSES
ROOT_URLCONF = settings.ROOT_URLCONF
TEMPLATES = settings.TEMPLATES
WSGI_APPLICATION = settings.WSGI_APPLICATION

# We can't take DATABASES from cove settings,
# ... otherwise the files appear under the BASE_DIR that is the Cove library install.
# That could get messy. We want them to appear in our directory.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': env('DB_NAME'),
    }
}

LANGUAGE_CODE = settings.LANGUAGE_CODE
TIME_ZONE = settings.TIME_ZONE
USE_I18N = settings.USE_I18N
USE_L10N = settings.USE_L10N
USE_TZ = settings.USE_TZ

# We can't take STATIC_URL and STATIC_ROOT from cove settings,
# ... otherwise the files appear under the BASE_DIR that is the Cove library install.
# and that doesn't work with our standard Apache setup.
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

LANGUAGES = settings.LANGUAGES
LOCALE_PATHS = settings.LOCALE_PATHS
LOCALE_PATHS += os.path.join(BASE_DIR, 'cove_iati', 'locale'),
LOGGING = settings.LOGGING

if getattr(settings, 'RAVEN_CONFIG', None):
    RAVEN_CONFIG = settings.RAVEN_CONFIG

INSTALLED_APPS = settings.INSTALLED_APPS + ('cove_iati', )
WSGI_APPLICATION = 'cove_iati.wsgi.application'
ROOT_URLCONF = 'cove_iati.urls'
COVE_CONFIG = {
    'app_name': 'cove_iati',
    'app_base_template': 'cove_iati/base.html',
    'app_verbose_name': 'IATI CoVE',
    'app_strapline': 'Convert, Validate, Explore IATI Data',
    'core_schema': {'activity': 'iati-activities-schema.xsd', 'organisation': 'iati-organisations-schema.xsd'},
    'supplementary_schema': {'common': 'iati-common.xsd', 'xml': 'xml.xsd'},
    'schema_host': 'https://raw.githubusercontent.com/IATI/IATI-Schemas/',
    'schema_version': '2.03',
    'schema_directory': 'iati_schemas',
    'root_id': None,
    'id_name': 'iati-identifier',
    'convert_titles': False,
    'input_methods': ['upload', 'url', 'text'],
    'support_email': None,
    'flatten_tool': {
        'disable_local_refs': True,
        'remove_empty_schema_columns': True,
        'xml_comment': 'Data generated by IATI CoVE. Built by Open Data Services Co-operative: http://iati.cove.opendataservices.coop/',
    },
    'hashcomments': True
}


# https://github.com/OpenDataServices/cove/issues/1098
FILE_UPLOAD_PERMISSIONS = 0o644
