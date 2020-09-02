from urllib.parse import urljoin

from django.conf import settings

from libcove.lib.common import SchemaJsonMixin


config = settings.COVE_CONFIG


class Schema360(SchemaJsonMixin):
    schema_host = config['schema_host']
    schema_name = config['schema_item_name']
    pkg_schema_name = config['schema_name']
    schema_url = urljoin(schema_host, schema_name)
    pkg_schema_url = urljoin(schema_host, pkg_schema_name)
