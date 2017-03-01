from cached_property import cached_property
import collections
from collections import OrderedDict
import json
import requests
import re
from urllib.parse import urlparse, urljoin

from flattentool.schema import get_property_type_set
import json_merge_patch
import jsonref
from jsonschema import FormatChecker, RefResolver
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator as validator

import cove.lib.tools as tools


uniqueItemsValidator = validator.VALIDATORS.pop("uniqueItems")

LANGUAGE_RE = re.compile("^(.*_(((([A-Za-z]{2,3}(-([A-Za-z]{3}(-[A-Za-z]{3}){0,2}))?)|[A-Za-z]{4}|[A-Za-z]{5,8})(-([A-Za-z]{4}))?(-([A-Za-z]{2}|[0-9]{3}))?(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-([0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(x(-[A-Za-z0-9]{1,8})+))?)|(x(-[A-Za-z0-9]{1,8})+)))$")

validation_error_lookup = {"date-time": "Date is not in the correct format",
                           "uri": "Invalid 'uri' found",
                           "string": "Value is not a string",
                           "integer": "Value is not a integer",
                           "number": "Value is not a number",
                           "object": "Value is not an object",
                           "array": "Value is not an array"}


class CustomJsonrefLoader(jsonref.JsonLoader):
    def __init__(self, **kwargs):
        self.schema_url = kwargs.pop('schema_url', None)
        super().__init__(**kwargs)

    def get_remote_json(self, uri, **kwargs):
        # ignore url in ref apart from last part
        uri = self.schema_url + uri.split('/')[-1]
        if uri[:4] == 'http':
            return super().get_remote_json(uri, **kwargs)
        else:
            with open(uri) as schema_file:
                return json.load(schema_file, **kwargs)


class CustomRefResolver(RefResolver):
    def __init__(self, *args, **kw):
        self.schema_url = kw.pop('schema_url')
        super().__init__(*args, **kw)

    def resolve_remote(self, uri):
        uri = self.schema_url + uri.split('/')[-1]
        document = self.store.get(uri)
        if document:
            return document

        if self.schema_url.startswith("http"):
            return super().resolve_remote(uri)
        else:
            with open(uri) as schema_file:
                result = json.load(schema_file)
            if self.cache_remote:
                self.store[uri] = result
            return result


class Schema():
    def __init__(self, package_name, package_host=None):
        self.package_name = package_name
        self.package_host = package_host or ''
        self.package_url = urljoin(self.package_host, self.package_name)

    @cached_property
    def _package_data(self):
        if urlparse(self.package_url).scheme == 'http':
            return requests.get(self.package_url).text
        else:
            with open(self.package_url) as openfile:
                return openfile.read()

    @cached_property
    def release_url(self):
        releases = self._package_schema_data.get('releases')
        url = releases and releases.get('items') and releases.get('items').get('$ref')
        return url

    @property
    def extensions(self):
        return self.ref_schema_data.get('extensions') or None

    @property
    def extension_errors(self):
        return None

    @property
    def deref_schema_data(self):
        return jsonref.loads(self._package_data, loader=CustomJsonrefLoader(schema_url=self.package_host),
                             object_pairs_hook=OrderedDict)

    @property
    def ref_schema_data(self):
        return json.loads(self.pkg_schema_data)

    def get_extended_schema_data(self, deref=True):
        if self.extensions:
            schema_data = self.ref_schema_data
            for url in self.extensions:
                i = url.rfind('/')
                url = '{}/{}'.format(url[:i], 'release-schema.json')
                extension = requests.get(url)
                if extension.ok:
                    try:
                        extension_data = extension.json()
                    except json.JSONDecodeError:
                        continue
                else:
                    continue

            extended_schema_data = json_merge_patch(schema_data, extension_data)
            if deref:
                extended_schema_text = json.dumps(extended_schema_data)
                extended_schema_data = jsonref.loads(
                    extended_schema_text,
                    loader=CustomJsonrefLoader(schema_url=self.schema_host),
                    object_pairs_hook=OrderedDict
                )
            return extended_schema_data

        return None


def unique_ids(validator, ui, instance, schema):
    if ui and validator.is_type(instance, "array"):
        non_unique_ids = set()
        all_ids = set()
        for item in instance:
            try:
                item_id = item.get('id')
            except AttributeError:
                # if item is not a dict
                item_id = None
            if item_id and not isinstance(item_id, list) and not isinstance(item_id, dict):
                if item_id in all_ids:
                    non_unique_ids.add(item_id)
                all_ids.add(item_id)
            else:
                # if there is any item without an id key, or the item is not a dict
                # revert to original validator
                for error in uniqueItemsValidator(validator, ui, instance, schema):
                    yield error
                return

        if non_unique_ids:
            yield ValidationError("Non-unique ID Values (first 3 shown):  {}".format(", ".join(str(x) for x in list(non_unique_ids)[:3])))


def required_draft4(validator, required, instance, schema):
    if not validator.is_type(instance, "object"):
        return
    for property in required:
        if property not in instance:
            yield ValidationError(property)


validator.VALIDATORS.pop("patternProperties")
validator.VALIDATORS["uniqueItems"] = unique_ids
validator.VALIDATORS["required"] = required_draft4


def fields_present_generator(json_data, prefix=''):
    if not isinstance(json_data, dict):
        return
    for key, value in json_data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield from fields_present_generator(item, prefix + '/' + key)
            yield prefix + '/' + key
        elif isinstance(value, dict):
            yield from fields_present_generator(value, prefix + '/' + key)
            yield prefix + '/' + key
        else:
            yield prefix + '/' + key


def get_fields_present(*args, **kwargs):
    counter = collections.Counter()
    counter.update(fields_present_generator(*args, **kwargs))
    return dict(counter)


def schema_dict_fields_generator(schema_dict):
    if 'properties' in schema_dict:
        for property_name, value in schema_dict['properties'].items():
            if 'oneOf' in value:
                property_schema_dicts = value['oneOf']
            else:
                property_schema_dicts = [value]
            for property_schema_dict in property_schema_dicts:
                property_type_set = get_property_type_set(property_schema_dict)
                if 'object' in property_type_set:
                    for field in schema_dict_fields_generator(property_schema_dict):
                        yield '/' + property_name + field
                elif 'array' in property_type_set:
                    fields = schema_dict_fields_generator(property_schema_dict['items'])
                    for field in fields:
                        yield '/' + property_name + field
                yield '/' + property_name


def get_schema_data(schema_url, schema_name):
    if schema_url[:4] == 'http':
        r = requests.get(schema_url + schema_name)
        json_text = r.text
    else:
        with open(schema_url + schema_name) as schema_file:
            json_text = schema_file.read()

    return jsonref.loads(json_text, loader=CustomJsonrefLoader(schema_url=schema_url), object_pairs_hook=OrderedDict)


def get_schema_fields(schema_url, schema_name):
    return set(schema_dict_fields_generator(get_schema_data(schema_url, schema_name)))


def get_counts_additional_fields(schema_url, schema_name, json_data, context, current_app):
    fields_present = get_fields_present(json_data)
    schema_fields = get_schema_fields(schema_url, schema_name)
    data_only_all = set(fields_present) - schema_fields
    data_only = set()
    for field in data_only_all:
        parent_field = "/".join(field.split('/')[:-1])
        # only take fields with parent in schema (and top level fields)
        # to make results less verbose
        if not parent_field or parent_field in schema_fields:
            if current_app == 'cove-ocds':
                if LANGUAGE_RE.search(field.split('/')[-1]):
                    continue
            data_only.add(field)

    return [('/'.join(key.split('/')[:-1]), key.split('/')[-1], fields_present[key]) for key in data_only]


def get_schema_validation_errors(json_data, schema_url, schema_name, current_app, cell_source_map, heading_source_map):
    if schema_url.startswith("http"):
        schema = requests.get(schema_url + schema_name).json()
    else:
        with open(schema_url + schema_name) as schema_file:
            schema = json.load(schema_file)

    validation_errors = collections.defaultdict(list)
    format_checker = FormatChecker()
    if current_app == 'cove-360':
        format_checker.checkers['date-time'] = (tools.datetime_or_date, ValueError)
    for n, e in enumerate(validator(schema, format_checker=format_checker, resolver=CustomRefResolver('', schema, schema_url=schema_url)).iter_errors(json_data)):
        message = e.message
        path = "/".join(str(item) for item in e.path)
        path_no_number = "/".join(str(item) for item in e.path if not isinstance(item, int))

        validator_type = e.validator
        if e.validator in ('format', 'type'):
            validator_type = e.validator_value
            if isinstance(e.validator_value, list):
                validator_type = e.validator_value[0]

            new_message = validation_error_lookup.get(validator_type)
            if new_message:
                message = new_message

        value = {"path": path}
        cell_reference = cell_source_map.get(path)

        if cell_reference:
            first_reference = cell_reference[0]
            if len(first_reference) == 4:
                value["sheet"], value["col_alpha"], value["row_number"], value["header"] = first_reference
            if len(first_reference) == 2:
                value["sheet"], value["row_number"] = first_reference

        if not isinstance(e.instance, (dict, list)):
            value["value"] = e.instance

        if e.validator == 'required':
            field_name = e.message
            if len(e.path) > 2:
                if isinstance(e.path[-2], int):
                    parent_name = e.path[-1]
                else:
                    parent_name = e.path[-2]

                field_name = str(parent_name) + ":" + e.message
            heading = heading_source_map.get(path_no_number + '/' + e.message)
            if heading:
                field_name = heading[0][1]
                value['header'] = heading[0][1]
            message = "'{}' is missing but required".format(field_name)
        if e.validator == 'enum':
            header = value.get('header')
            if not header:
                header = e.path[-1]
            message = "Invalid code found in '{}'".format(header)

        unique_validator_key = [validator_type, message, path_no_number]
        validation_errors[json.dumps(unique_validator_key)].append(value)
    return dict(validation_errors)


def _get_schema_deprecated_paths(schema_name, schema_url, obj=None, current_path=(), deprecated_paths=None):
    '''Get a list of deprecated paths and explanations for deprecation in a schema.

    Deprecated paths are given as tuples of tuples:
    ((path, to, field), (deprecation_version, description))
    '''
    if deprecated_paths is None:
        deprecated_paths = []

    if schema_url:
        obj = get_schema_data(schema_url, schema_name)

    for prop, value in obj['properties'].items():
        if current_path:
            path = current_path + (prop,)
        else:
            path = (prop,)

        if "deprecated" in value and path not in deprecated_paths:
                deprecated_paths.append((
                    path,
                    (value['deprecated']['deprecatedVersion'], value['deprecated']['description'])
                ))

        if value.get('type') == 'object':
            _get_schema_deprecated_paths(None, None, value, path, deprecated_paths)
        elif value.get('type') == 'array' and value['items'].get('properties'):
            _get_schema_deprecated_paths(None, None, value['items'], path, deprecated_paths)

    return deprecated_paths


def _get_json_data_generic_paths(json_data, path=(), generic_paths=None):
    '''Transform json data into a dictionary with keys made of json paths.

   Key are json paths (as tuples). Values are dictionaries with keys including specific
   indexes (which are not including in the top level keys), eg:

   {'a': 'I am', 'b': ['a', 'list'], 'c': [{'ca': 'ca1'}, {'ca': 'ca2'}, {'cb': 'cb'}]}

   will produce:

   {('a',): {('a',): I am'},
    ('b',): {{(b, 0), 'a'}, {('b', 1): 'list'}},
    ('c', 'ca'): {('c', 0, 'ca'): 'ca1', ('c', 1, 'ca'): 'ca2'},
    ('c', 'cb'): {('c', 1, 'ca'): 'cb'}}
    '''
    if generic_paths is None:
        generic_paths = {}

    if isinstance(json_data, dict):
        iterable = list(json_data.items())
        if not iterable:
            generic_paths[path] = {}
    else:
        iterable = list(enumerate(json_data))
        if not iterable:
            generic_paths[path] = []

    for key, value in iterable:
        if isinstance(value, (dict, list)):
            _get_json_data_generic_paths(value, path + (key,), generic_paths)
        else:
            generic_key = tuple(i for i in path + (key,) if type(i) != int)
            if generic_paths.get(generic_key):
                generic_paths[generic_key][path + (key,)] = value
            else:
                generic_paths[generic_key] = {path + (key,): value}

    return generic_paths


def get_json_data_deprecated_fields(schema_name, schema_url, json_data):
    deprecated_schema_paths = _get_schema_deprecated_paths(schema_name, schema_url)
    paths_in_data = _get_json_data_generic_paths(json_data)
    deprecated_paths_in_data = [path for path in deprecated_schema_paths if path[0] in paths_in_data]

    # Generate an OrderedDict sorted by deprecated field names (keys) mapping
    # to a unordered tuple of tuples:
    # {deprecated_field: ((path, path... ), (version, description))}
    deprecated_fields = OrderedDict()
    for generic_path in sorted(deprecated_paths_in_data, key=lambda tup: tup[0][-1]):
        deprecated_fields[generic_path[0][-1]] = (
            tuple((key for key in paths_in_data[generic_path[0]].keys())),
            generic_path[1]
        )

    # Order the path tuples in values for deprecated_fields.
    deprecated_fields_output = OrderedDict()
    for field, paths in deprecated_fields.items():
        sorted_paths = tuple(sorted(paths[0]))
        slashed_paths = tuple(("/".join((map(str, sort_path[:-1]))) for sort_path in sorted_paths))
        deprecated_fields_output[field] = {"paths": slashed_paths, "explanation": paths[1]}

    return deprecated_fields_output
