from cove import settings
import os
import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(  # set default values and casting
    DB_NAME=(str, os.path.join(BASE_DIR, 'db.sqlite3')),
    SENTRY_DSN=(str, ''),
)

# We use the setting to choose whether to show the section about Sentry in the
# terms and conditions
SENTRY_DSN = env('SENTRY_DSN')

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import ignore_logger

    ignore_logger('django.security.DisallowedHost')
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[DjangoIntegration()]
    )

DEALER_TYPE = 'git'

PIWIK = settings.PIWIK
GOOGLE_ANALYTICS_ID = settings.GOOGLE_ANALYTICS_ID

# We can't take MEDIA_ROOT and MEDIA_URL from cove settings,
# ... otherwise the files appear under the BASE_DIR that is the Cove library install.
# That could get messy. We want them to appear in our directory.
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.DEBUG
ALLOWED_HOSTS = settings.ALLOWED_HOSTS
MIDDLEWARE = settings.MIDDLEWARE
MIDDLEWARE += ('dealer.contrib.django.Middleware',)
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
LOCALE_PATHS += os.path.join(BASE_DIR, 'cove_360', 'locale'),
LOGGING = settings.LOGGING

if getattr(settings, 'RAVEN_CONFIG', None):
    RAVEN_CONFIG = settings.RAVEN_CONFIG

INSTALLED_APPS = settings.INSTALLED_APPS + ('cove_360', )
WSGI_APPLICATION = 'cove_360.wsgi.application'
ROOT_URLCONF = 'cove_360.urls'
COVE_CONFIG = {
    'app_name': 'cove_360',
    'app_base_template': 'cove_360/base.html',
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
    'support_email': 'support@threesixtygiving.org',
    'hashcomments': True
}

# https://github.com/OpenDataServices/cove/issues/1098
FILE_UPLOAD_PERMISSIONS = 0o644
