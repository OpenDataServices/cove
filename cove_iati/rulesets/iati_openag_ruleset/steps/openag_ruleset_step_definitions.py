'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
from behave import then

from cove.lib.common import get_orgids_prefixes
from cove_iati.lib.exceptions import RuleSetStepException
from cove_iati.rulesets.utils import get_xpaths, get_full_xpath

ORGIDS_PREFIXES = get_orgids_prefixes()


@then('at least one `{xpath_expression}` element is expected')
def step_openag_expected(context, xpath_expression):
    xpaths = get_xpaths(context.xml, xpath_expression)
    if not xpaths:
        errors = [{
            'message': 'the activity should include at least one <{}> element'.format(xpath_expression),
            'path': get_full_xpath(context.xml, context.xml)
        }]
        raise RuleSetStepException(context, errors)


@then('every `{xpath_expression}` must have `{attribute}` attribute')
def step_openag_tag_attribute_expected(context, xpath_expression, attribute):
    xpaths = get_xpaths(context.xml, xpath_expression)
    msg = '{} element must have @{} attribute'
    fail = False

    if xpaths:
        errors = []
        for xpath in xpaths:
            attrib = xpath.attrib
            required_attrib = attrib.get(attribute)
            if not required_attrib:
                    errors.append({'message': msg.format(xpath_expression, attribute),
                                   'path': get_full_xpath(context.xml, xpath)})
                    fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('every `{attribute}` must be equal to `{any_value}`')
def step_openag_tag_attribute_accepted_values(context, attribute, any_value):
    xpaths = get_xpaths(context.xml, context.xpath_expression)
    msg = '"{}" is not a valid value for @{} attribute (it should be "{}")'
    fail = False

    if xpaths:
        errors = []
        for xpath in xpaths:
            element_attrs = xpath.attrib
            matching_value = any([element_attrs.get(attribute) == val for val in any_value.split(' or ')])
            if not matching_value:
                errors.append({'message': msg.format(element_attrs.get(attribute), attribute, any_value),
                               'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
                fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('every `{xpath_expression1}` must include `{xpath_expression2}` element')
def step_openag_location_id_expected(context, xpath_expression1, xpath_expression2):
    xpaths = get_xpaths(context.xml, xpath_expression1)
    msg = '{} must contain a {} element'
    fail = False

    if xpaths:
        errors = []
        for xpath in xpaths:
            has_xpath_expression2 = xpath.find(xpath_expression2)
            if not has_xpath_expression2:
                errors.append({'message': msg.format(xpath_expression1, xpath_expression2),
                               'path': get_full_xpath(context.xml, xpath)})
                fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('`{attribute}` id attribute should start with an org-ids prefix')
def step_openag_org_id_prefix_expected(context, attribute):
    xpaths = get_xpaths(context.xml, context.xpath_expression)
    msg = '@{} {} does not start with a recognised org-ids prefix'
    fail = False

    if xpaths:
        errors = []
        for xpath in xpaths:
            attr_id = xpath.attrib.get(attribute, '')
            if attr_id[:6].upper() not in ORGIDS_PREFIXES:
                errors.append({'message': msg.format(attr_id, attribute),
                               'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
                fail = True
    if fail:
        raise RuleSetStepException(context, errors)
