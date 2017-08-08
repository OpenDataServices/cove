from collections import OrderedDict
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

INSTALLED_APPS = settings.INSTALLED_APPS + ('cove_ocds', )
WSGI_APPLICATION = 'cove_ocds.wsgi.application'
ROOT_URLCONF = 'cove_ocds.urls'
COVE_CONFIG = {
    'app_name': 'cove_ocds',
    'app_base_template': 'cove_ocds/base.html',
    'app_verbose_name': 'Open Contracting Data Standard Validator',
    'app_strapline': 'Validate and Explore your data.',
    'schema_name': {'release': 'release-package-schema.json', 'record': 'record-package-schema.json'},
    'schema_item_name': 'release-schema.json',
    'schema_host': None,
    'schema_version_choices': OrderedDict((  # {version: (display, url)}
        ('1.0', ('1.0', 'http://standard.open-contracting.org/schema/1__0__3/')),
        ('1.1', ('1.1', 'http://standard.open-contracting.org/schema/1__1__1/')),
    )),
    'schema_codelists': OrderedDict((  # {version: codelist_dir}
        ('1.1', 'https://raw.githubusercontent.com/open-contracting/standard/1.1/standard/schema/codelists/'),
    )),
    'root_list_path': 'releases',
    'root_id': 'ocid',
    'convert_titles': False,
    'input_methods': ['upload', 'url', 'text'],
    'support_email': 'data@open-contracting.org'
}

# Set default schema version to the latest version
COVE_CONFIG['schema_version'] = list(COVE_CONFIG['schema_version_choices'].keys())[-1]
