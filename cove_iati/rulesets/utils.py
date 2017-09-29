import datetime

from cove_iati.lib.exceptions import RuleSetStepException


def invalid_date_format(xpath, date_str):
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


def register_ruleset_errors(func):
    def wrapper(*args, **kwargs):
        context, errors = func(*args, **kwargs)
        if errors:
            raise RuleSetStepException(context, errors)
    return wrapper
