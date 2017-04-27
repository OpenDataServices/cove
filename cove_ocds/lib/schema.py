import os
import json
from copy import deepcopy
from urllib.parse import urljoin, urlparse

import json_merge_patch
import requests
from cached_property import cached_property
from django.conf import settings

from cove.lib.common import SchemaJsonMixin, schema_dict_fields_generator


config = settings.COVE_CONFIG


class SchemaOCDS(SchemaJsonMixin):
    release_schema_name = config['schema_item_name']
    release_pkg_schema_name = config['schema_name']['release']
    record_pkg_schema_name = config['schema_name']['record']
    version_choices = config['schema_version_choices']
    default_version = config['schema_version']
    default_schema_host = version_choices[default_version][1]
    default_release_schema_url = urljoin(default_schema_host, release_schema_name)

    def __init__(self, select_version=None, release_data=None):
        '''Build the schema object using an specific OCDS schema version
        
        The version used will be select_version, release_data.get('version') or
        default version, in that order. Invalid version choices in select_version or
        release_data will be skipped and registered as self.invalid_version_argument
        and self.invalid_version_data respectively.
        '''
        self.version = self.default_version
        self.invalid_version_argument = False
        self.invalid_version_data = False
        self.schema_host = self.default_schema_host
        self.extensions = {}
        self.invalid_extension = {}
        self.extended = False
        self.extended_schema_file = None
        self.extended_schema_url = None
        self.codelists = config['schema_codelists']['1.1']

        if select_version:
            try:
                self.version_choices[select_version]
            except KeyError:
                select_version = None
                self.invalid_version_argument = True
                print('Not a valid value for `version` argument: using version in the release '
                      'data or the default version if version is missing in the release data')
            else:
                self.version = select_version
                self.schema_host = self.version_choices[select_version][1]

        if release_data:
            data_extensions = release_data.get('extensions', {})
            if data_extensions:
                self.extensions = {ext: tuple() for ext in data_extensions}
            if not select_version:
                release_version = release_data.get('version')
                if release_version:
                    version_choice = self.version_choices.get(release_version)
                    if version_choice:
                        self.version = release_version
                        self.schema_host = version_choice[1]
                    else:
                        self.invalid_version_data = True
        else:
            pass

        self.release_schema_url = urljoin(self.schema_host, self.release_schema_name)
        self.release_pkg_schema_url = urljoin(self.schema_host, self.release_pkg_schema_name)
        self.record_pkg_schema_url = urljoin(self.schema_host, self.record_pkg_schema_name)

    def get_release_schema_obj(self, deref=False):
        release_schema_obj = self._release_schema_obj
        if self.extended_schema_file:
            with open(self.extended_schema_file) as fp:
                release_schema_obj = json.load(fp)
        elif self.extensions:
            release_schema_obj = deepcopy(self._release_schema_obj)
            self.apply_extensions(release_schema_obj)
        if deref:
            if self.extended:
                extended_release_schema_str = json.dumps(release_schema_obj)
                release_schema_obj = self.deref_schema(extended_release_schema_str)
            else:
                release_schema_obj = self.deref_schema(self.release_schema_str)
        return release_schema_obj

    def get_release_pkg_schema_obj(self, deref=False):
        package_schema_obj = self._release_pkg_schema_obj
        if deref:
            deref_release_schema_obj = self.get_release_schema_obj(deref=True)
            if self.extended:
                package_schema_obj = deepcopy(self._release_pkg_schema_obj)
                package_schema_obj['properties']['releases']['items'] = {}
                release_pkg_schema_str = json.dumps(package_schema_obj)
                package_schema_obj = self.deref_schema(release_pkg_schema_str)
                package_schema_obj['properties']['releases']['items'].update(deref_release_schema_obj)
            else:
                package_schema_obj = self.deref_schema(self.release_pkg_schema_str)
        return package_schema_obj

    def apply_extensions(self, schema_obj):
        if not self.extensions:
            return
        for extensions_descriptor_url in self.extensions.keys():
            i = extensions_descriptor_url.rfind('/')
            url = '{}/{}'.format(extensions_descriptor_url[:i], 'release-schema.json')

            try:
                extension = requests.get(url)
            except requests.exceptions.RequestException:
                self.invalid_extension[extensions_descriptor_url] = 'fetching failed'
                continue
            if extension.ok:
                try:
                    extension_data = extension.json()
                except json.JSONDecodeError:
                    self.invalid_extension[extensions_descriptor_url] = 'invalid JSON'
                    continue
            else:
                self.invalid_extension[extensions_descriptor_url] = '{}: {}'.format(extension.status_code,
                                                                                    extension.reason.lower())
                continue

            schema_obj = json_merge_patch.merge(schema_obj, extension_data)
            extensions_descriptor = requests.get(extensions_descriptor_url).json()
            self.extensions[extensions_descriptor_url] = (url, extensions_descriptor['name'],
                                                          extensions_descriptor['description'])
            self.extended = True

    def create_extended_release_schema_file(self, upload_dir, upload_url):
        filepath = os.path.join(upload_dir, 'extended_release_schema.json')

        # Always replace any existing extended schema file
        if os.path.exists(filepath):
            os.remove(filepath)
            self.extended_schema_file = None
            self.extended_schema_url = None

        if not self.extensions:
            return

        release_schema_obj = self.get_release_schema_obj()
        if not self.extended:
            return

        with open(filepath, 'w') as fp:
            release_schema_str = json.dumps(release_schema_obj, indent=4)
            fp.write(release_schema_str)

        self.extended_schema_file = filepath
        self.extended_schema_url = urljoin(upload_url, 'extended_release_schema.json')

    @cached_property
    def record_pkg_schema_str(self):
        uri_scheme = urlparse(self.record_pkg_schema_url).scheme
        if uri_scheme == 'http' or uri_scheme == 'https':
            return requests.get(self.record_pkg_schema_url).text
        else:
            with open(self.record_pkg_schema_url) as fp:
                return fp.read()

    @property
    def _record_pkg_schema_obj(self):
        return json.loads(self.record_pkg_schema_str)

    def get_record_pkg_schema_obj(self, deref=False):
        if deref:
            return self.deref_schema(self.record_pkg_schema_str)
        return self._record_pkg_schema_obj

    def get_record_pkg_schema_fields(self):
        return set(schema_dict_fields_generator(self.get_record_pkg_schema_obj(deref=True)))
