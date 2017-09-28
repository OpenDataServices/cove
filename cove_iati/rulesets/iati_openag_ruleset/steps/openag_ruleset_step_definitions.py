'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
from behave import given, then

from cove.lib.common import get_orgids_prefixes
from cove_iati.lib.exceptions import RuleSetStepException


def get_xpaths(context, xpath_expression):
    nsmap = context.xml.getparent().nsmap
    xpaths = context.xml.xpath(xpath_expression, namespaces=nsmap)
    return xpaths


@given('an Open Agriculture IATI activity')
def step_openag_iati_activity(context):
    assert True


@given('{xpath_expression} elements')
def step_openag_element(context, xpath_expression):
    assert True


@given('{xpath_expression} organisation')
def step_openag_organisation(context, xpath_expression):
    context.xpath_expression = xpath_expression
    assert True


@then('at least one `{xpath_expression}` element is expected')
def step_openag_expected(context, xpath_expression):
    xpaths = get_xpaths(context, xpath_expression)
    if not xpaths:
        tree = context.xml.getroottree()
        errors = [{
            'message': 'the activity should include at least one <{}> element'.format(xpath_expression),
            'path': tree.getpath(context.xml)
        }]
        raise RuleSetStepException(context, errors)


@then('every `{xpath_expression}` must have `{attribute}` attribute')
def step_openag_tag_attribute_expected(context, xpath_expression, attribute):
    # Add to context for steps with no xpath_expression
    context.xpath_expression = xpath_expression
    xpaths = get_xpaths(context, xpath_expression)
    fail = False

    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        for xpath in xpaths:
            attrib = xpath.attrib
            required_attrib = attrib.get(attribute)
            if not required_attrib:
                    msg = '{} element must have @{} attribute'.format(xpath_expression, attribute)
                    errors.append({'message': msg, 'path': tree.getpath(xpath)})
                    fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('every `{attribute}` must be equal to `{any_value}`')
def step_openag_tag_attribute_accepted_values(context, attribute, any_value):
    xpaths = get_xpaths(context, context.xpath_expression)
    fail = False

    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        for xpath in xpaths:
            element_attrs = xpath.attrib
            matching_value = any([element_attrs.get(attribute) == val for val in any_value.split(' or ')])

            if not matching_value:
                msg = '@{} attribute must be equal to "{}" (it is "{}")'
                msg = msg.format(attribute, any_value, element_attrs.get(attribute))
                errors.append({'message': msg, 'path': tree.getpath(xpath)})
                fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('every `{xpath_expression1}` must include `{xpath_expression2}` element')
def step_openag_location_id_expected(context, xpath_expression1, xpath_expression2):
    xpaths = get_xpaths(context, xpath_expression1)
    fail = False

    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        for xpath in xpaths:
            has_xpath_expression2 = xpath.find(xpath_expression2)
            if not has_xpath_expression2:
                msg = '{} must contain a {} element'.format(xpath_expression1, xpath_expression2)
                errors.append({'message': msg, 'path': tree.getpath(xpath)})
                fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('`{attribute}` attribute should start with an org-id prefix')
def step_openag_org_id_prefix_expected(context, attribute):
    print(context.xpath_expression)
