from collections import defaultdict
import json


def group_validation_errors(validation_errors):
    validation_errors_grouped = defaultdict(list)
    for error_json, values in validation_errors:
        error = json.loads(error_json)
        if error['message_type'] == 'required':
            validation_errors_grouped['required'].append((error_json, values))
        elif error['message_type'] in ['format', 'pattern', 'number', 'string',
                                       'date-time', 'uri', 'object', 'integer', 'array']:
            validation_errors_grouped['format'].append((error_json, values))
        else:
            validation_errors_grouped['other'].append((error_json, values))
    return validation_errors_grouped
