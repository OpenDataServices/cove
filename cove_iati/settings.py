import sys
if "pytest" not in sys.modules:
    # Check that we can import defusedexpat, as this will protect us against
    # some XML attacks in xmltodict
    # Needs a noqa comment as we don't actually use it here
    import defusedexpat  # noqa: F401

# Needs a noqa comment to come after the above import
from cove import settings  # noqa: E408

PIWIK = settings.PIWIK
GOOGLE_ANALYTICS_ID = settings.GOOGLE_ANALYTICS_ID
MEDIA_ROOT = settings.MEDIA_ROOT
MEDIA_URL = settings.MEDIA_URL
DEALER_TYPE = settings.DEALER_TYPE
SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.DEBUG
ALLOWED_HOSTS = settings.ALLOWED_HOSTS
MIDDLEWARE_CLASSES = settings.MIDDLEWARE_CLASSES
ROOT_URLCONF = settings.ROOT_URLCONF
TEMPLATES = settings.TEMPLATES
WSGI_APPLICATION = settings.WSGI_APPLICATION
DATABASES = settings.DATABASES
LANGUAGE_CODE = settings.LANGUAGE_CODE
TIME_ZONE = settings.TIME_ZONE
USE_I18N = settings.USE_I18N
USE_L10N = settings.USE_L10N
USE_TZ = settings.USE_TZ
STATIC_URL = settings.STATIC_URL
STATIC_ROOT = settings.STATIC_ROOT
LANGUAGES = settings.LANGUAGES
LOCALE_PATHS = settings.LOCALE_PATHS
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
    'root_list_path': 'iati-activity',
    'root_id': None,
    'id_name': 'iati-identifier',
    'convert_titles': False,
    'input_methods': ['upload', 'url', 'text'],
    'support_email': None
}
