from cove import settings

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

INSTALLED_APPS = settings.INSTALLED_APPS + ('cove-360', )
WSGI_APPLICATION = 'cove-360.wsgi.application'
ROOT_URLCONF = 'cove-360.urls'
COVE_CONFIG = {
    'app_name': 'cove-360',
    'app_verbose_name': '360Giving Data Quality Tool',
    'app_strapline': 'Convert, Validate, Explore 360Giving Data',
    'schema_name': '360-giving-package-schema.json',
    'schema_item_name': '360-giving-schema.json',
    'schema_host': 'https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/',
    'schema_version': None,
    'schema_version_choices': None,
    'root_list_path': 'grants',
    'root_id': '',
    'convert_titles': True,
    'input_methods': ['upload', 'url', 'text'],
    'support_email': 'support@threesixtygiving.org'
}
