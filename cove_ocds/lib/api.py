import re


class APIException(Exception):
    pass


def context_api_transform(context):
    validation_errors = context.get('validation_errors')
    context['validation_errors'] = []

    context.pop('validation_errors_count')

    extensions = context.get('extensions')
    context['extensions'] = {}

    deprecated_fields = context.get('deprecated_fields')
    context['deprecated_fields'] = []

    additional_fields = context.pop('data_only')
    context['additional_fields'] = []
    context.pop('additional_fields_count')

    if validation_errors:
        for error_group in validation_errors:
            error_type, error_description, error_field = [
                re.sub('(\[?|\s?)\"\]?', '', err) for err in error_group[0].split(',')
            ]
            for path_value in error_group[1]:
                context['validation_errors'].append({
                    'type': error_type,
                    'field': error_field,
                    'description': error_description,
                    'path': path_value.get('path', ''),
                    'value': path_value.get('value', '')
                })

    if extensions:
        invalid_extensions = extensions.get('invalid_extension')
        context['extensions']['extensions'] = []
        for key, value in extensions['extensions'].items():
            if key not in invalid_extensions:
                context['extensions']['extensions'].append(value)
        context['extensions']['invalid_extensions'] = []
        for key, value in invalid_extensions.items():
            context['extensions']['invalid_extensions'].append([key, value])
        context['extensions']['extended_schema_url'] = extensions['extended_schema_url']
        context['extensions']['is_extended_schema'] = extensions['is_extended_schema']

    if deprecated_fields:
        for key, value in deprecated_fields.items():
            value.update({'field': key})
            context['deprecated_fields'].append(value)

    if additional_fields:
        for field_group in additional_fields:
            context['additional_fields'].append({
                'path': field_group[0],
                'field': field_group[1],
                'usage_count': field_group[2]
            })

    return context
