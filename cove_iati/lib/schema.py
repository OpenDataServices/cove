import os
from urllib.parse import urljoin

import requests
from django.conf import settings

config = settings.COVE_CONFIG

current_dir = os.path.dirname(os.path.realpath(__file__))


class SchemaIATI():
    default_schema_host = config['schema_host']
    default_version = config['schema_version']
    activity_schema_name = config['core_schema']['activity']
    organization_schema_name = config['core_schema']['organization']
    common_schema_name = config['supplementary_schema']['common']
    xml_schema_name = config['supplementary_schema']['xml']

    def __init__(self, select_version=None):
        self.version = select_version or self.default_version
        self.schema_host = '{}/version-{}/'.format(self.default_schema_host, self.version)
        self.schema_directory = os.path.join(current_dir, '../../', config['app_name'], config['schema_directory'], self.version)

        if not os.path.isdir(self.schema_directory):
            os.makedirs(self.schema_directory)

            for filename in [self.activity_schema_name, self.organization_schema_name,
                             self.common_schema_name, self.xml_schema_name]:
                with open(os.path.join(self.schema_directory, filename), 'w') as schema_file:
                    schema_file_url = urljoin(self.schema_host, filename)
                    xml_text = requests.get(schema_file_url).text
                    schema_file.write(xml_text)

        self.activity_schema = os.path.join(self.schema_directory, self.activity_schema_name)
        self.organization_schema = os.path.join(self.schema_directory, self.organization_schema_name)
        self.common_schema = os.path.join(self.schema_directory, self.common_schema_name)
