import strict_rfc3339
import datetime
from functools import wraps  # use this to preserve function signatures and docstrings


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


def get_generic_paths(path, flattened, obj):
    '''Transform a dict into another dict with keys made of json paths.

   Key are json paths (as tuples) with list indexes represented as '[]', which
   means 'at an unspecified position in an array'. Values are dictionaries with
   keys replacing '[]' with the specific index, eg:

   {'a': 'I am', 'b': ['a', 'list'], 'c': [{'ca': 'ca1'}, {'ca': 'ca2'}, {'cb': 'cb'}]}

   will produce:

   {('a',): {('a',): I am'},
    ('b', '[]''): {{(b, 0), 'a'}, {('b', 1): 'list'}},
    ('c', '[]', 'ca'): {('c', 0, 'ca'): 'ca1', ('c', 1, 'ca'): 'ca2'},
    ('c', '[]', 'cb'): {('c', 1, 'ca'): 'cb'}}
    '''
    if isinstance(obj, dict):
        iterable = list(obj.items())
        if not iterable:
            flattened[path] = {}
    else:
        iterable = list(enumerate(obj))
        if not iterable:
            flattened[path] = []

    for key, value in iterable:
        if isinstance(value, (dict, list)):
            get_generic_paths(path + (key,), flattened, value)
        else:
            generic_key = tuple('[]' if type(i) == int else i for i in path + (key,))
            if flattened.get(generic_key):
                flattened[generic_key][path + (key,)] = value
            else:
                flattened[generic_key] = {path + (key,): value}

    return flattened
