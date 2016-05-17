import collections
from collections import OrderedDict
import requests
import jsonref
from flattentool.schema import get_property_type_set
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator as validator
from jsonschema import FormatChecker

from cove.lib.tools import *


uniqueItemsValidator = validator.VALIDATORS.pop("uniqueItems")


def uniqueIds(validator, uI, instance, schema):
    if (
        uI and
        validator.is_type(instance, "array")
    ):
        non_unique_ids = set()
        all_ids = set()
        for item in instance:
            try:
                item_id = item.get('id')
            except AttributeError:
                # if item is not a dict
                item_id = None
            if item_id and not isinstance(item_id, list):
                if item_id in all_ids:
                    non_unique_ids.add(item_id)
                all_ids.add(item_id)
            else:
                # if there is any item without an id key, or the item is not a dict
                # revert to original validator
                for error in uniqueItemsValidator(validator, uI, instance, schema):
                    yield error
                return

        if non_unique_ids:
            yield ValidationError("Non-unique ID Values (first 3 shown):  {}".format(", ".join(list(non_unique_ids)[:3])))


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


def get_schema_fields(schema_filename):
    r = requests.get(schema_filename)
    return set(schema_dict_fields_generator(jsonref.loads(r.text, object_pairs_hook=OrderedDict)))


def get_counts_additional_fields(schema_url, json_data, context, current_app):
    fields_present = get_fields_present(json_data)
    schema_fields = get_schema_fields(schema_url)
    data_only_all = set(fields_present) - schema_fields
    data_only = set()
    for field in data_only_all:
        parent_field = "/".join(field.split('/')[:-1])
        # only take fields with parent in schema (and top level fields)
        # to make results less verbose
        if not parent_field or parent_field in schema_fields:
            print(field, current_app)
            if '_' in field.split('/')[-1] and current_app == 'cove-ocds':
                context['language_additional_field_warning'] = True
            data_only.add(field)

    return [('/'.join(key.split('/')[:-1]), key.split('/')[-1], fields_present[key]) for key in data_only]


def get_schema_validation_errors(json_data, schema_url, current_app):
    schema = requests.get(schema_url).json()
    validation_errors = collections.defaultdict(list)
    format_checker = FormatChecker()
    if current_app == 'cove-360':
        format_checker.checkers['date-time'] = (datetime_or_date, ValueError)
    for n, e in enumerate(validator(schema, format_checker=format_checker).iter_errors(json_data)):
        validation_errors[e.message].append("/".join(str(item) for item in e.path))
    return dict(validation_errors)
