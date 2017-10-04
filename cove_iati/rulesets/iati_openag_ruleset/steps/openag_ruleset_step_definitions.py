'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
import re

from behave import then

from cove.lib.common import get_orgids_prefixes
from cove_iati.rulesets.utils import get_full_xpath, get_xpaths, register_ruleset_errors

ORGIDS_PREFIXES = get_orgids_prefixes()


@then('at least one `{xpath_expression}` element is expected')
@register_ruleset_errors('openag')
def step_openag_expected(context, xpath_expression):
    errors = []
    if not get_xpaths(context.xml, xpath_expression):
        errors = [{
            'message': 'the activity should include at least one {} element'.format(xpath_expression),
            'path': get_full_xpath(context.xml, context.xml)
        }]
    return context, errors


@then('every `{xpath_expression}` must have `{attribute}` attribute')
@register_ruleset_errors('openag')
def step_openag_tag_attribute_expected(context, xpath_expression, attribute):
    errors = []
    fail_msg = '{} element must have @{} attribute'

    for xpath in get_xpaths(context.xml, xpath_expression):
        attrib = xpath.attrib
        required_attrib = attrib.get(attribute)
        if not required_attrib:
                errors.append({'message': fail_msg.format(xpath_expression, attribute),
                               'path': get_full_xpath(context.xml, xpath)})
    return context, errors


@then('every `{attribute}` must be equal to `{any_value}`')
@register_ruleset_errors('openag')
def step_openag_tag_attribute_accepted_values(context, attribute, any_value):
    errors = []
    fail_msg = '"{}" is not a valid value for @{} attribute (it should be "{}")'

    for xpath in get_xpaths(context.xml, context.xpath_expression):
        element_attrs = xpath.attrib
        matching_value = any([element_attrs.get(attribute) == val for val in any_value.split(' or ')])
        if not matching_value:
            errors.append({'message': fail_msg.format(element_attrs.get(attribute), attribute, any_value),
                           'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
    return context, errors


@then('every `{xpath_expression1}` must include `{xpath_expression2}` element')
@register_ruleset_errors('openag')
def step_openag_location_id_expected(context, xpath_expression1, xpath_expression2):
    errors = []
    fail_msg = '{} must contain a {} element'

    for xpath in get_xpaths(context.xml, xpath_expression1):
        has_xpath_expression2 = get_xpaths(xpath, xpath_expression2)
        if not has_xpath_expression2:
            errors.append({'message': fail_msg.format(xpath_expression1, xpath_expression2),
                           'path': get_full_xpath(context.xml, xpath)})
    return context, errors


@then('`{attribute}` id attribute must start with an org-ids prefix')
@register_ruleset_errors('openag')
def step_openag_org_id_prefix_expected(context, attribute):
    errors = []
    fail_msg = '@{} {} does not start with a recognised org-ids prefix'

    for xpath in get_xpaths(context.xml, context.xpath_expression):
        attr_id = xpath.attrib.get(attribute, '')
        for prefix in ORGIDS_PREFIXES:
            if re.match('^%s' % prefix, attr_id):
                break
        else:
            errors.append({'message': fail_msg.format(attribute, attr_id),
                           'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
    return context, errors
