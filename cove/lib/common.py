import collections
import csv
import datetime
import functools
import json
import os
import re
from collections import OrderedDict
from urllib.parse import urlparse, urljoin

import jsonref
import requests
from cached_property import cached_property
from flattentool.schema import get_property_type_set
from flattentool import unflatten
from jsonschema import FormatChecker, RefResolver
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator as validator

from cove.lib.exceptions import cove_spreadsheet_conversion_error
from cove.lib.tools import decimal_default


uniqueItemsValidator = validator.VALIDATORS.pop("uniqueItems")
LANGUAGE_RE = re.compile("^(.*_(((([A-Za-z]{2,3}(-([A-Za-z]{3}(-[A-Za-z]{3}){0,2}))?)|[A-Za-z]{4}|[A-Za-z]{5,8})(-([A-Za-z]{4}))?(-([A-Za-z]{2}|[0-9]{3}))?(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-([0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(x(-[A-Za-z0-9]{1,8})+))?)|(x(-[A-Za-z0-9]{1,8})+)))$")
validation_error_lookup = {'date-time': 'Date is not in the correct format',
                           'uri': 'Invalid \'uri\' found',
                           'string': 'Value is not a string',
                           'integer': 'Value is not a integer',
                           'number': 'Value is not a number',
                           'object': 'Value is not an object',
                           'array': 'Value is not an array'}


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
        self.schema_file = kw.pop('schema_file', None)
        self.schema_url = kw.pop('schema_url', '')
        super().__init__(*args, **kw)

    def resolve_remote(self, uri):
        schema_name = self.schema_file or uri.split('/')[-1]
        uri = urljoin(self.schema_url, schema_name)
        document = self.store.get(uri)

        if document:
            return document
        if self.schema_url.startswith("http"):
            return super().resolve_remote(uri)
        else:
            with open(uri) as schema_file:
                result = json.load(schema_file)

        add_is_codelist(result)
        self.store[uri] = result
        return result


class SchemaJsonMixin():
    @cached_property
    def release_schema_str(self):
        return requests.get(self.release_schema_url).text

    @cached_property
    def release_pkg_schema_str(self):
        uri_scheme = urlparse(self.release_pkg_schema_url).scheme
        if uri_scheme == 'http' or uri_scheme == 'https':
            return requests.get(self.release_pkg_schema_url).text
        else:
            with open(self.release_pkg_schema_url) as fp:
                return fp.read()

    @property
    def _release_schema_obj(self):
        return json.loads(self.release_schema_str, object_pairs_hook=OrderedDict)

    @property
    def _release_pkg_schema_obj(self):
        return json.loads(self.release_pkg_schema_str)

    def deref_schema(self, schema_str):
        loader = CustomJsonrefLoader(schema_url=self.schema_host)
        try:
            deref_obj = jsonref.loads(schema_str, loader=loader, object_pairs_hook=OrderedDict)
            # Force evaluation of jsonref.loads here
            repr(deref_obj)
            return deref_obj
        except jsonref.JsonRefError as e:
            self.json_deref_error = e.message
            return {}

    def get_release_schema_obj(self, deref=False):
        if deref:
            return self.deref_schema(self.release_schema_str)
        return self._release_schema_obj

    def get_release_pkg_schema_obj(self, deref=False):
        if deref:
            return self.deref_schema(self.release_pkg_schema_str)
        return self._release_pkg_schema_obj

    def get_release_pkg_schema_fields(self):
        return set(schema_dict_fields_generator(self.get_release_pkg_schema_obj(deref=True)))


def common_checks_context(upload_dir, json_data, schema_obj, schema_name, context, extra_checkers=None,
                          fields_regex=False, api=False, cache=True):
    schema_version = getattr(schema_obj, 'version', None)
    schema_version_choices = getattr(schema_obj, 'version_choices', None)

    if schema_version:
        schema_version_display_choices = tuple(
            (version, display_url[0]) for version, display_url in schema_version_choices.items()
        )
        context['version_used'] = schema_version
        if not api:
            context.update({
                'version_display_choices': schema_version_display_choices,
                'version_used_display': schema_version_choices[schema_version][0]}
            )

    additional_fields = sorted(get_counts_additional_fields(json_data, schema_obj, schema_name,
                                                            context, fields_regex=fields_regex))
    context.update({
        'data_only': additional_fields,
        'additional_fields_count': sum(item[2] for item in additional_fields)
    })

    cell_source_map = {}
    heading_source_map = {}
    if context['file_type'] != 'json':  # Assume it is csv or xlsx
        with open(os.path.join(upload_dir, 'cell_source_map.json')) as cell_source_map_fp:
            cell_source_map = json.load(cell_source_map_fp)

        with open(os.path.join(upload_dir, 'heading_source_map.json')) as heading_source_map_fp:
            heading_source_map = json.load(heading_source_map_fp)

    validation_errors_path = os.path.join(upload_dir, 'validation_errors-2.json')
    if os.path.exists(validation_errors_path):
        with open(validation_errors_path) as validation_error_fp:
            validation_errors = json.load(validation_error_fp)
    else:
        validation_errors = get_schema_validation_errors(json_data, schema_obj, schema_name,
                                                         cell_source_map, heading_source_map,
                                                         extra_checkers=extra_checkers)
        if cache:
            with open(validation_errors_path, 'w+') as validation_error_fp:
                validation_error_fp.write(json.dumps(validation_errors, default=decimal_default))

    extensions = None
    if getattr(schema_obj, 'extensions', None):
        extensions = {
            'extensions': schema_obj.extensions,
            'invalid_extension': schema_obj.invalid_extension,
            'is_extended_schema': schema_obj.extended,
            'extended_schema_url': schema_obj.extended_schema_url
        }

    context.update({
        'schema_url': schema_obj.release_pkg_schema_url,
        'extensions': extensions,
        'validation_errors': sorted(validation_errors.items()),
        'validation_errors_count': sum(len(value) for value in validation_errors.values()),
        'deprecated_fields': get_json_data_deprecated_fields(json_data, schema_obj),
        'common_error_types': []
    })
    if not api:
        context['json_data'] = json_data

    return {
        'context': context,
        'cell_source_map': cell_source_map,
    }


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
            msg = "Non-unique ID Values (first 3 shown):  {}"
            yield ValidationError(msg.format(", ".join(str(x) for x in list(non_unique_ids)[:3])))


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


def get_counts_additional_fields(json_data, schema_obj, schema_name, context, fields_regex=False):
    if schema_name == 'record-package-schema.json':
        schema_fields = schema_obj.get_record_pkg_schema_fields()
    else:
        schema_fields = schema_obj.get_release_pkg_schema_fields()

    fields_present = get_fields_present(json_data)
    data_only_all = set(fields_present) - schema_fields
    data_only = set()
    for field in data_only_all:
        parent_field = "/".join(field.split('/')[:-1])
        # only take fields with parent in schema (and top level fields)
        # to make results less verbose
        if not parent_field or parent_field in schema_fields:
            if fields_regex:
                if LANGUAGE_RE.search(field.split('/')[-1]):
                    continue
            data_only.add(field)

    return [('/'.join(key.split('/')[:-1]), key.split('/')[-1], fields_present[key]) for key in data_only]


def get_schema_validation_errors(json_data, schema_obj, schema_name, cell_src_map, heading_src_map, extra_checkers=None):
    if schema_name == 'record-package-schema.json':
        pkg_schema_obj = schema_obj.get_record_pkg_schema_obj()
    else:
        pkg_schema_obj = schema_obj.get_release_pkg_schema_obj()

    validation_errors = collections.defaultdict(list)
    format_checker = FormatChecker()
    if extra_checkers:
        format_checker.checkers.update(extra_checkers)

    if getattr(schema_obj, 'extended', None):
        resolver = CustomRefResolver('', pkg_schema_obj, schema_file=schema_obj.extended_schema_file)
    else:
        resolver = CustomRefResolver('', pkg_schema_obj, schema_url=schema_obj.schema_host)

    our_validator = validator(pkg_schema_obj, format_checker=format_checker, resolver=resolver)
    for n, e in enumerate(our_validator.iter_errors(json_data)):
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
        cell_reference = cell_src_map.get(path)

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
                if isinstance(e.path[-1], int):
                    parent_name = e.path[-2]
                else:
                    parent_name = e.path[-1]

                field_name = str(parent_name) + ":" + e.message
            heading = heading_src_map.get(path_no_number + '/' + e.message)
            if heading:
                field_name = heading[0][1]
                value['header'] = heading[0][1]
            message = "'{}' is missing but required".format(field_name)
        if e.validator == 'enum':
            if "isCodelist" in e.schema:
                continue
            header = value.get('header')
            if not header:
                header = e.path[-1]
            message = "Invalid code found in '{}'".format(header)

        unique_validator_key = [validator_type, message, path_no_number]
        validation_errors[json.dumps(unique_validator_key)].append(value)
    return dict(validation_errors)


def _get_schema_deprecated_paths(schema_obj, obj=None, current_path=(), deprecated_paths=None):
    '''Get a list of deprecated paths and explanations for deprecation in a schema.

    Deprecated paths are given as tuples of tuples:
    ((path, to, field), (deprecation_version, description))
    '''
    if deprecated_paths is None:
        deprecated_paths = []

    if schema_obj:
        obj = schema_obj.get_release_pkg_schema_obj(deref=True)

    for prop, value in obj.get('properties', {}).items():
        if current_path:
            path = current_path + (prop,)
        else:
            path = (prop,)

        if path not in deprecated_paths:
            if "deprecated" in value:
                deprecated_paths.append((
                    path,
                    (value['deprecated']['deprecatedVersion'], value['deprecated']['description'])
                ))
            elif getattr(value, '__reference__', None) and "deprecated" in value.__reference__:
                deprecated_paths.append((
                    path,
                    (value.__reference__['deprecated']['deprecatedVersion'],
                     value.__reference__['deprecated']['description'])
                ))

        if value.get('type') == 'object':
            _get_schema_deprecated_paths(None, value, path, deprecated_paths)
        elif value.get('type') == 'array' and value['items'].get('properties'):
            _get_schema_deprecated_paths(None, value['items'], path, deprecated_paths)

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
        generic_key = tuple(i for i in path + (key,) if type(i) != int)
        
        if generic_paths.get(generic_key):
            generic_paths[generic_key][path + (key,)] = value
        else:
            generic_paths[generic_key] = {path + (key,): value}

        if isinstance(value, (dict, list)):
            _get_json_data_generic_paths(value, path + (key,), generic_paths)

    return generic_paths


def get_json_data_deprecated_fields(json_data, schema_obj):
    deprecated_schema_paths = _get_schema_deprecated_paths(schema_obj)
    paths_in_data = _get_json_data_generic_paths(json_data)
    deprecated_paths_in_data = [path for path in deprecated_schema_paths if path[0] in paths_in_data]
    # Generate an OrderedDict sorted by deprecated field names (keys) mapping
    # to a unordered tuple of tuples:
    # {deprecated_field: ((path, path... ), (version, description))}
    deprecated_fields = OrderedDict()
    for generic_path in sorted(deprecated_paths_in_data, key=lambda tup: tup[0][-1]):
        deprecated_fields[generic_path[0][-1]] = tuple()

        # Be defensive against invalid schema data and corner cases.
        # e.g. (invalid OCDS data):
        # {"version":"1.1", "releases":{"buyer":{"additionalIdentifiers":[]}}}
        if hasattr(paths_in_data[generic_path[0]], "keys"):
            deprecated_fields[generic_path[0][-1]] += (tuple(key for key in paths_in_data[generic_path[0]].keys()),
                                                       generic_path[1])
        else:
            deprecated_fields[generic_path[0][-1]] += ((generic_path[0],), generic_path[1])

    # Order the path tuples in values for deprecated_fields.
    deprecated_fields_output = OrderedDict()
    for field, paths in deprecated_fields.items():
        sorted_paths = tuple(sorted(paths[0]))

        # Avoid adding terminal paths for array indexes as only whole arrays can be deprecated.
        # TODO: check, is that true for all cases?
        slashed_paths = tuple(
            ("/".join((map(str, sort_path[:-1])))
             for sort_path in sorted_paths if type(sort_path[-1]) != int)
        )
        deprecated_fields_output[field] = {"paths": slashed_paths, "explanation": paths[1]}

    return deprecated_fields_output


def add_is_codelist(obj):
    ''' This is needed so that we can detect enums that are arrays as the jsonschema library does not
    give you any parent information and the codelist property is on the parent in this case. Only applies to
    release.tag in core schema at the moment.'''

    for prop, value in obj.get('properties', {}).items():
        if "codelist" in value:
            if 'array' in value.get('type', ''):
                value['items']['isCodelist'] = True
            else:
                value['isCodelist'] = True

        if value.get('type') == 'object':
            add_is_codelist(value)
        elif value.get('type') == 'array' and value['items'].get('properties'):
            add_is_codelist(value['items'])

    for value in obj.get("definitions", {}).values():
        if "properties" in value:
            add_is_codelist(value)


def _get_schema_codelist_paths(schema_obj, obj=None, current_path=(), codelist_paths=None):
    '''Get a dict of codelist paths including the filename and if they are open.

    codelist paths are given as tuples of tuples:
        {("path", "to", "codelist"): (filename, open?), ..}
    '''
    if codelist_paths is None:
        codelist_paths = {}

    if schema_obj:
        obj = schema_obj.get_release_pkg_schema_obj(deref=True)

    for prop, value in obj.get('properties', {}).items():
        if current_path:
            path = current_path + (prop,)
        else:
            path = (prop,)

        if "codelist" in value and path not in codelist_paths:
            codelist_paths[path] = (value['codelist'], value.get('openCodelist', False))

        if value.get('type') == 'object':
            _get_schema_codelist_paths(None, value, path, codelist_paths)
        elif value.get('type') == 'array' and value['items'].get('properties'):
            _get_schema_codelist_paths(None, value['items'], path, codelist_paths)

    return codelist_paths


@functools.lru_cache()
def _load_codelists(codelist_url, unique_files):
    codelists = {}
    for codelist_file in unique_files:
        try:
            response = requests.get(codelist_url + codelist_file)
            response.raise_for_status()
            reader = csv.DictReader(line.decode("utf8") for line in response.iter_lines())
            codelists[codelist_file] = {}
            for record in reader:
                code = record.get('Code') or record.get('code')
                title = record.get('Title') or record.get('Title_en')
                codelists[codelist_file][code] = title

        except requests.exceptions.RequestException:
            codelists = {}
            break

    return codelists


def _generate_data_path(json_data, path=()):
    if not json_data or not isinstance(json_data, dict):
        return path
    for key, value in json_data.items():
        if not value:
            continue
        if isinstance(value, list):
            if isinstance(value[0], dict):
                for num, item in enumerate(value):
                    yield from _generate_data_path(item, path + (key, num))
            else:
                yield path + (key,), value
        elif isinstance(value, dict):
            yield from _generate_data_path(value, path + (key,))
        else:
            yield path + (key,), value


def get_additional_codelist_values(schema_obj, codelist_url, json_data):
    if not codelist_url:
        return {}
    codelist_schema_paths = _get_schema_codelist_paths(schema_obj)
    unique_files = frozenset(value[0] for value in codelist_schema_paths.values())
    codelists = _load_codelists(codelist_url, unique_files)

    additional_codelist_values = {}
    for path, values in _generate_data_path(json_data):
        if not isinstance(values, list):
            values = [values]

        path_no_num = tuple(key for key in path if isinstance(key, str))

        if path_no_num not in codelist_schema_paths:
            continue

        codelist, isopen = codelist_schema_paths[path_no_num]

        codelist_values = codelists.get(codelist)
        if not codelist_values:
            continue

        for value in values:
            if str(value) in codelist_values:
                continue
            if path_no_num not in additional_codelist_values:
                additional_codelist_values[path_no_num] = {
                    "path": "/".join(path_no_num[:-1]),
                    "field": path_no_num[-1],
                    "codelist": codelist,
                    "codelist_url": codelist_url + codelist,
                    "isopen": isopen,
                    "values": set(),
                    #"location_values": []
                }

            additional_codelist_values[path_no_num]['values'].add(str(value))
            #additional_codelist_values[path_no_num]['location_values'].append((path, value))

    return additional_codelist_values


@cove_spreadsheet_conversion_error
def get_spreadsheet_meta_data(upload_dir, file_name, schema, file_type='xlsx', name='Meta'):
    if file_type == 'csv':
        input_name = upload_dir
    else:
        input_name = file_name
    output_name = os.path.join(upload_dir, 'metatab.json')

    unflatten(
        input_name=input_name,
        output_name=output_name,
        input_format=file_type,
        metatab_only=True,
        metatab_schema=schema,
        metatab_name=name,
        metatab_vertical_orientation=True
    )

    with open(output_name) as metatab_data:
        metatab_json = json.load(metatab_data)
    return metatab_json


def get_orgids_prefixes(orgids_url=None):
    local_org_ids_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'org-ids.json')
    today = datetime.date.today()
    get_remote_file = False
    first_request = False

    if not orgids_url:
        orgids_url = 'http://org-id.guide/download.json'

    if os.path.exists(local_org_ids_file):
        with open(local_org_ids_file) as fp:
            org_ids = json.load(fp)
        date_str = org_ids.get('downloaded', '2000-1-1')
        date_downloaded = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        if date_downloaded != today:
            get_remote_file = True
    else:
        get_remote_file = True
        first_request = True

    if get_remote_file:
        try:
            org_ids = requests.get(orgids_url).json()
            org_ids['downloaded'] = "%s" % today
            with open(local_org_ids_file, 'w') as fp:
                json.dump(org_ids, fp, indent=2)
        except requests.exceptions.RequestException:
            if first_request:
                raise  # First time ever request fails
            pass  # Update fails

    return [org_list['code'] for org_list in org_ids['lists']]
