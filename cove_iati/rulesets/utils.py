import datetime
from functools import wraps

from cove_iati.lib.exceptions import RuleSetStepException


def invalid_date_format(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return True
    return False


def get_child_full_xpath(parent_xobj, child_xobj):
    '''Return full xpath for a xml object in the context of a parent object'''
    tree = parent_xobj.getroottree()
    return tree.getpath(child_xobj)


def get_xobjects(xobj, xpath_expression):
    '''Given a xpath, return a list of xml objects out of a parent xml object'''
    nsmap = xobj.getparent().nsmap
    xobjects = xobj.xpath(xpath_expression, namespaces=nsmap)
    return xobjects


def register_ruleset_errors(namespaces=None):
    '''Raise a RuleSetStepException to register errors (bdd-tester/behave).

    Also, check the date for the presence of declared namespaces required
    to apply the rule.

    Args:
        namespaces: list or tuple with namespace names
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if namespaces:
                context = args[0]
                nsmap = context.xml.getparent().nsmap
                for ns in namespaces:
                    if not nsmap.get(ns):
                        msg = 'rule not applied: the data does not define "{}" namespace (@xmlns:{})'
                        errors = [{
                            'message': msg.format(ns, ns),
                            'path': '/iati-activities/@xmlns'
                        }]
                        raise RuleSetStepException(context, errors)

            context, errors = func(*args, **kwargs)
            if errors:
                raise RuleSetStepException(context, errors)

        return wrapper
    return decorator
