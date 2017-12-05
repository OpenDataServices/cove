'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
from decimal import Decimal
import datetime
import re

from behave import given, then

from cove_iati.rulesets.utils import invalid_date_format, get_child_full_xpath, get_xobjects, register_ruleset_errors


@given('an IATI activity')
def step_given_iati_activity(context):
    context.xpath_expression = '.'


@given('`{xpath_expression}` organisations')
def step_given_organisations(context, xpath_expression):
    context.xpath_expression = xpath_expression


@given('`{xpath_expression}` elements')
def step_given_elements(context, xpath_expression):
    context.xpath_expression = xpath_expression


@then('`{xpath}` must be today or in the past')
@register_ruleset_errors()
def step_must_be_today_or_past(context, xpath):
    errors = []
    today = datetime.date.today()
    parents = get_xobjects(context.xml, context.xpath_expression)

    for parent in parents:
        date_attrs = get_xobjects(parent, xpath)

        if not date_attrs:
            continue

        date_attr = date_attrs[0]

        if invalid_date_format(date_attr):
            continue

        date = datetime.datetime.strptime(date_attr, '%Y-%m-%d').date()
        if date > today:
            errors.append({'explanation': '{} must be on or before today ({})'.format(date, today),
                           'path': get_child_full_xpath(context.xml, date_attr)})
    return context, errors


@then('iati-identifier text should match the regex `{regex_str}`')
@register_ruleset_errors()
def step_iati_id_text_match_regex(context, regex_str):
    regex = re.compile(regex_str)
    errors = []

    xpath = get_xobjects(context.xml, context.xpath_expression)
    if xpath:
        xpath = xpath[0]
        fail_msg = 'Text does not match the regex {}'
        text_str = xpath.text
        if not regex.match(text_str):
            errors = [{'explanation': fail_msg.format(text_str, regex_str),
                       'path': '{}/text()'.format(get_child_full_xpath(context.xml, xpath))}]
    return context, errors


@then('`{attribute}` attribute should match the regex `{regex_str}`')
@register_ruleset_errors()
def step_attribute_match_regex(context, attribute, regex_str):
    regex = re.compile(regex_str)
    errors = []
    fail_msg = '{} does not match the regex {}'

    for xpath in get_xobjects(context.xml, context.xpath_expression):
        if attribute not in xpath.attrib:
            continue
        attr_str = xpath.attrib[attribute]
        if not regex.match(attr_str):
            errors.append({'explanation': fail_msg.format(attr_str, regex_str),
                           'path': '{}/@{}'.format(get_child_full_xpath(context.xml, xpath), attribute)})
    return context, errors


@then('either `{xpath_expression1}` or `{xpath_expression2}` is expected')
@register_ruleset_errors()
def step_either_or_expected(context, xpath_expression1, xpath_expression2):
    errors = []
    fail_msg_neither = 'Neither {} nor {} have been found'
    parents = get_xobjects(context.xml, context.xpath_expression)

    for parent in parents:
        xpaths1 = get_xobjects(parent, xpath_expression1)
        xpaths2 = get_xobjects(parent, xpath_expression2)

        if not xpaths1 and not xpaths2:
            errors.append({'explanation': fail_msg_neither.format(xpath_expression1, xpath_expression2),
                       'path': get_child_full_xpath(context.xml, context.xml)})

    return context, errors


@then('either `{xpath_expression1}` or `{xpath_expression2}` is expected, but not both')
@register_ruleset_errors()
def step_either_or_expected_not_both(context, xpath_expression1, xpath_expression2):
    errors = []
    fail_msg_neither = 'Neither {} nor {} have been found'
    fail_msg_both = 'Either {} or {} are expected (not both)'
    xpaths1 = get_xobjects(context.xml, xpath_expression1)
    xpaths2 = get_xobjects(context.xml, xpath_expression2)
    
    if not xpaths1 and not xpaths2:
        errors = [{'explanation': fail_msg_neither.format(xpath_expression1, xpath_expression2),
                   'path': get_child_full_xpath(context.xml, context.xml)}]

    if xpaths1 and xpaths2:
        msg = fail_msg_both.format(xpath_expression1, xpath_expression2)
        if len(xpaths1) == len(xpaths2):
            zipped_xpaths = zip(xpaths1, xpaths2)
            for tup_xpath1, tup_xpath2 in zipped_xpaths:
                errors = [{
                    'explanation': msg,
                    'path': '{} & {}'.format(get_child_full_xpath(context.xml, tup_xpath1),
                                             get_child_full_xpath(context.xml, tup_xpath2))
                }]
        else:
            for xpath in xpaths2:
                errors.append({
                    'explanation': msg,
                    'path': '{} & {}'.format(get_child_full_xpath(context.xml, xpaths1[0]),
                                             get_child_full_xpath(context.xml, xpath))
                })
    return context, errors


@then('`{xpath_expression}` is not expected')
@register_ruleset_errors()
def step_not_expected(context, xpath_expression):
    errors = []

    for xpath in get_xobjects(context.xml, xpath_expression):
        errors.append({'explanation': '`{}` is not expected'.format(xpath_expression),
                       'path': get_child_full_xpath(context.xml, xpath)})
    return context, errors


@then('`{xpath1}` must be chronologically before `{xpath2}`')
@register_ruleset_errors()
def step_start_date_before_end_date(context, xpath1, xpath2):
    parents = get_xobjects(context.xml, context.xpath_expression)

    errors = []
    for parent in parents:
        start_date_attrs = get_xobjects(parent, xpath1)
        end_date_attrs = get_xobjects(parent, xpath2)

        if not start_date_attrs or not end_date_attrs:
            continue

        start_date_attr = start_date_attrs[0]
        end_date_attr = end_date_attrs[0]

        if not invalid_date_format(start_date_attr) and not invalid_date_format(end_date_attr):
            start_date = datetime.datetime.strptime(start_date_attr, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date_attr, '%Y-%m-%d').date()
            if start_date >= end_date:
                fail_msg = 'Start date ({}) must be before end date ({})'
                path_attr1 = get_child_full_xpath(context.xml, start_date_attr)
                path_attr2 = get_child_full_xpath(context.xml, end_date_attr)
                errors.append({
                    'explanation': fail_msg.format(start_date_attr, end_date_attr),
                    'path': '{} & {}'.format(path_attr1, path_attr2)
                })
    return context, errors


@then(u'`{attribute}` attribute must sum to 100')
@register_ruleset_errors()
def step_impl(context, attribute):
    elements = get_xobjects(context.xml, context.xpath_expression)
    errors = []
    
    if len(elements) == 0 or (len(elements) == 1 and elements[0].attrib.get(attribute, '100') == '100'):
        return context, errors

    attr_sum = sum(Decimal(x.attrib.get(attribute)) for x in elements)
    if attr_sum != 100:
        errors.append({'explanation': '{}/@{} adds up to {}% only'.format(context.xpath_expression, attribute, attr_sum),
                       'path': ' & '.join(get_child_full_xpath(context.xml, element) for element in elements)})

    return context, errors
