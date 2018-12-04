from urllib.parse import urljoin

from django.conf import settings

from libcove.lib.common import SchemaJsonMixin


config = settings.COVE_CONFIG


class Schema360(SchemaJsonMixin):
    schema_host = config['schema_host']
    release_schema_name = config['schema_item_name']
    release_pkg_schema_name = config['schema_name']
    release_schema_url = urljoin(schema_host, release_schema_name)
    release_pkg_schema_url = urljoin(schema_host, release_pkg_schema_name)
