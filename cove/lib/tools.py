import datetime
import strict_rfc3339
from functools import lru_cache, wraps  # use this to preserve function signatures and docstrings
from decimal import Decimal

import requests

from . exceptions import UnrecognisedFileType


def ignore_errors(f):
    @wraps(f)
    def ignore(json_data, *args, ignore_errors=False, return_on_error={}, **kwargs):
        if ignore_errors:
            try:
                return f(json_data, *args, **kwargs)
            except (KeyError, TypeError, IndexError, AttributeError, ValueError):
                return return_on_error
        else:
            return f(json_data, *args, **kwargs)
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
    if not instance:
        raise ValueError
    result = strict_rfc3339.validate_rfc3339(instance)
    if result:
        return result
    return datetime.datetime.strptime(instance, "%Y-%m-%d")


def get_file_type(file):
    if isinstance(file, str):
        name = file.lower()
    else:
        name = file.name.lower()
    if name.endswith('.json'):
        return 'json'
    elif name.endswith('.xlsx'):
        return 'xlsx'
    elif name.endswith('.csv'):
        return 'csv'
    else:
        first_byte = file.read(1)
        if first_byte in [b'{', b'[']:
            return 'json'
        else:
            raise UnrecognisedFileType


# From http://bugs.python.org/issue16535
class NumberStr(float):
    def __init__(self, o):
        # We don't call the parent here, since we're deliberately altering it's functionality
        # pylint: disable=W0231
        self.o = o

    def __repr__(self):
        return str(self.o)

    # This is needed for this trick to work in python 3.4
    def __float__(self):
        return self


def decimal_default(o):
    if isinstance(o, Decimal):
        if int(o) == o:
            return int(o)
        else:
            return NumberStr(o)
    raise TypeError(repr(o) + " is not JSON serializable")


@lru_cache(maxsize=64)
def cached_get_request(url):
    return requests.get(url)
