import re


class APIException(Exception):
    pass


def context_api_transform(context):
    validation_errors = context.get('validation_errors')
    context['validation_errors'] = []

    if validation_errors:
            for error_group in validation_errors:
                error_description = error_group[0][5:]
                error_description = re.sub('(\[?|\s?)\"\]?', '', error_description)
                for path_value in error_group[1]:
                    context['validation_errors'].append({
                        'description': error_description,
                        'path': path_value.get('path', ''),
                        'value': path_value.get('value', '')
                    })

    return context
