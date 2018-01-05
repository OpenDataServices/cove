import os
import json
from copy import deepcopy
from urllib.parse import urljoin, urlparse

import json_merge_patch
import requests
from cached_property import cached_property
from django.conf import settings
from django.utils import translation


from cove.lib.common import SchemaJsonMixin, schema_dict_fields_generator
from cove.lib.tools import cached_get_request


config = settings.COVE_CONFIG


class SchemaOCDS(SchemaJsonMixin):
    release_schema_name = config['schema_item_name']
    release_pkg_schema_name = config['schema_name']['release']
    record_pkg_schema_name = config['schema_name']['record']
    version_choices = config['schema_version_choices']
    default_version = config['schema_version']
    default_schema_host = version_choices[default_version][1]

    def __init__(self, select_version=None, release_data=None, cache_schema=False):
        '''Build the schema object using an specific OCDS schema version
        
        The version used will be select_version, release_data.get('version') or
        default version, in that order. Invalid version choices in select_version or
        release_data will be skipped and registered as self.invalid_version_argument
        and self.invalid_version_data respectively.
        '''
        self.version = self.default_version
        self.schema_host = self.default_schema_host
        self.cache_schema = cache_schema

        # Missing package is only for original json data
        self.missing_package = False
        if release_data:
            if 'version' not in release_data:
                self.version = '1.0'
                self.schema_host = self.version_choices['1.0'][1]
            if 'releases' not in release_data and 'records' not in release_data:
                self.missing_package = True

        self.invalid_version_argument = False
        self.invalid_version_data = False
        self.json_deref_error = None
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
            else:
                self.version = select_version
                self.schema_host = self.version_choices[select_version][1]

        if hasattr(release_data, 'get'):
            data_extensions = release_data.get('extensions', {})
            if data_extensions:
                self.extensions = {ext: tuple() for ext in data_extensions if type(ext) == str}
            if not select_version:
                release_version = release_data and release_data.get('version')
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
        package_schema_obj = deepcopy(self._release_pkg_schema_obj)
        if deref:
            if self.extended:
                deref_release_schema_obj = self.get_release_schema_obj(deref=True)
                package_schema_obj['properties']['releases']['items'] = {}
                release_pkg_schema_str = json.dumps(package_schema_obj)
                package_schema_obj = self.deref_schema(release_pkg_schema_str)
                package_schema_obj['properties']['releases']['items'].update(deref_release_schema_obj)
            else:
                return self.deref_schema(self.release_pkg_schema_str)
        return package_schema_obj

    def apply_extensions(self, schema_obj):
        if not self.extensions:
            return
        for extensions_descriptor_url in self.extensions.keys():
            i = extensions_descriptor_url.rfind('/')
            url = '{}/{}'.format(extensions_descriptor_url[:i], 'release-schema.json')

            try:
                if self.cache_schema:
                    extension = cached_get_request(url)
                else:
                    extension = requests.get(url)
            except requests.exceptions.RequestException:
                self.invalid_extension[extensions_descriptor_url] = 'fetching failed'
                continue

            if extension.ok:
                try:
                    extension_data = extension.json()
                except ValueError:  # would be json.JSONDecodeError for Python 3.5+
                    self.invalid_extension[extensions_descriptor_url] = 'release schema invalid JSON'
                    continue
            else:
                self.invalid_extension[extensions_descriptor_url] = '{}: {}'.format(extension.status_code,
                                                                                    extension.reason.lower())
                continue

            schema_obj = json_merge_patch.merge(schema_obj, extension_data)
            try:
                if self.cache_schema:
                    response = cached_get_request(extensions_descriptor_url)
                else:
                    response = requests.get(extensions_descriptor_url)
                extensions_descriptor = response.json()

            except ValueError:  # would be json.JSONDecodeError for Python 3.5+
                self.invalid_extension[extensions_descriptor_url] = 'invalid JSON'
                continue
            cur_language = translation.get_language()

            extension_description = {'url': url}

            # Section to be removed when extensions conform to new schema
            old_documentation_url = extensions_descriptor.get('documentation_url', '')
            if old_documentation_url and 'documentationUrl' not in extensions_descriptor:
                extensions_descriptor['documentationUrl'] = {'en': old_documentation_url}
            # End section

            for field in ['description', 'name', 'documentationUrl']:
                field_object = extensions_descriptor.get(field, {})
                if isinstance(field_object, str):
                    field_value = field_object
                else:
                    field_value = field_object.get(cur_language)
                    if not field_value:
                        field_value = field_object.get('en', '')
                extension_description[field] = field_value

            self.extensions[extensions_descriptor_url] = extension_description
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
            if self.cache_schema:
                response = cached_get_request(self.record_pkg_schema_url)
            else:
                response = requests.get(self.record_pkg_schema_url)
            return response.text
        else:
            with open(self.record_pkg_schema_url) as fp:
                return fp.read()

    @property
    def _record_pkg_schema_obj(self):
        return json.loads(self.record_pkg_schema_str)

    def get_record_pkg_schema_obj(self, deref=False):
        if deref:
            deref_package_schema = self.deref_schema(self.record_pkg_schema_str)
            if self.extended:
                deref_release_schema_obj = self.get_release_schema_obj(deref=True)
                deref_package_schema['properties']['records']['items']['properties']['compiledRelease'] = deref_release_schema_obj
                deref_package_schema['properties']['records']['items']['properties']['releases']['oneOf'][1] = deref_release_schema_obj
            return deref_package_schema
        return deepcopy(self._record_pkg_schema_obj)

    def get_record_pkg_schema_fields(self):
        return set(schema_dict_fields_generator(self.get_record_pkg_schema_obj(deref=True)))
