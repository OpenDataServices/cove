import datetime
from functools import wraps

from cove_iati.lib.exceptions import RuleSetStepException


def invalid_date_format(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return True
    return False


def get_full_xpath(xml, xpath):
    tree = xml.getroottree()
    return tree.getpath(xpath)


def get_xpaths(xml, xpath_expression):
    nsmap = xml.getparent().nsmap
    xpaths = xml.xpath(xpath_expression, namespaces=nsmap)
    return xpaths


def register_ruleset_errors(namespace=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if namespace:
                context = args[0]
                nsmap = context.xml.getparent().nsmap
                if not nsmap.get(namespace):
                    msg = 'rule not applied: the data does not define "{}" namespace (@xmlns:{})'
                    errors = [{
                        'message': msg.format(namespace, namespace),
                        'path': '/iati-activities/@xmlns'
                    }]
                    raise RuleSetStepException(context, errors)

            context, errors = func(*args, **kwargs)
            if errors:
                raise RuleSetStepException(context, errors)

        return wrapper
    return decorator
