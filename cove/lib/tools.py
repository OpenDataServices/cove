import datetime
import strict_rfc3339
from functools import wraps  # use this to preserve function signatures and docstrings

from . exceptions import UnrecognisedFileType


def ignore_errors(f):
    @wraps(f)
    def ignore(json_data, ignore_errors=False):
        if ignore_errors:
            try:
                return f(json_data)
            except (KeyError, TypeError, IndexError, AttributeError):
                return {}
        else:
            return f(json_data)
    return ignore


def to_list(item):
    if isinstance(item, list):
        return item
    return [item]


def get_no_exception(item, key, fallback):
    try:
        return item.get(key, fallback)
    except AttributeError:
        return fallback


def update_docs(document_parent, counter):
    count = 0
    documents = document_parent.get('documents', [])
    for document in documents:
        count += 1
        doc_type = document.get("documentType")
        if doc_type:
            counter.update([doc_type])
    return count


def datetime_or_date(instance):
    result = strict_rfc3339.validate_rfc3339(instance)
    if result:
        return result
    return datetime.datetime.strptime(instance, "%Y-%m-%d")


def get_file_type(file):
    name = file.name.lower()
    if name.endswith('.json'):
        return 'json'
    elif name.endswith('.xlsx'):
        return 'xlsx'
    elif name.endswith('.csv'):
        return 'csv'
    elif name.endswith('.xml'):
        return 'xml'
    else:
        first_byte = file.read(1)
        if first_byte in [b'{', b'[']:
            return 'json'
        else:
            raise UnrecognisedFileType
