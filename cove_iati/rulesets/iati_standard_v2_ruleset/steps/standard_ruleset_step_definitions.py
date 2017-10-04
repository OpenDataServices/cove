'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
import datetime
import re

from behave import given, then

from cove_iati.rulesets.utils import invalid_date_format, get_full_xpath, get_xpaths, register_ruleset_errors


@given('an IATI activity')
def step_given_iati_activity(context):
    assert True


@given('`{xpath_expression}` organisations')
def step_given_organisations(context, xpath_expression):
    context.xpath_expression = xpath_expression


@given('`{xpath_expression}` elements')
def step_given_elements(context, xpath_expression):
    context.xpath_expression = xpath_expression


@given('`{xpath_expression1}` plus `{xpath_expression2}`')
def step_given_two_different_elements(context, xpath_expression1, xpath_expression2):
    context.xpath_expression1 = xpath_expression1
    context.xpath_expression2 = xpath_expression2


@then('`{attribute}` attribute must be today or in the past')
@register_ruleset_errors()
def step_must_be_today_or_past(context, attribute):
    errors = []
    today = datetime.date.today()

    for xpath in get_xpaths(context.xml, context.xpath_expression):
        date_str = xpath.attrib.get(attribute)

        if invalid_date_format(date_str):
            continue

        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        if date > today:
            errors.append({'message': '{} must be on or before today ({})'.format(date, today),
                           'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
    return context, errors


@then('iati-identifier text should match the regex `{regex_str}`')
@register_ruleset_errors()
def step_iati_id_text_match_regex(context, regex_str):
    regex = re.compile(regex_str)
    errors = []

    xpath = get_xpaths(context.xml, context.xpath_expression)
    if xpath:
        xpath = xpath[0]
        fail_msg = 'Text does not match the regex {}'
        text_str = xpath.text
        if not regex.match(text_str):
            errors = [{'message': fail_msg.format(text_str, regex_str),
                       'path': '{}/text()'.format(get_full_xpath(context.xml, xpath))}]
    return context, errors


@then('`{attribute}` attribute should match the regex `{regex_str}`')
@register_ruleset_errors()
def step_attribute_match_regex(context, attribute, regex_str):
    regex = re.compile(regex_str)
    errors = []
    fail_msg = '{} does not match the regex {}'

    for xpath in get_xpaths(context.xml, context.xpath_expression):
        attr_str = xpath.attrib.get(attribute, '')
        if not regex.match(attr_str):
            errors.append({'message': fail_msg.format(attr_str, regex_str),
                           'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
    return context, errors


@then('either `{xpath_expression1}` or `{xpath_expression2}` is expected')
@register_ruleset_errors()
def step_either_or_expected(context, xpath_expression1, xpath_expression2):
    errors = []
    fail_msg_neither = 'Neither {} nor {} have been found'
    fail_msg_both = 'Either {} or {} are expected (not both)'
    xpaths1 = get_xpaths(context.xml, xpath_expression1)
    xpaths2 = get_xpaths(context.xml, xpath_expression2)
    
    if not xpaths1 and not xpaths2:
        errors = [{'message': fail_msg_neither.format(xpath_expression1, xpath_expression2),
                   'path': get_full_xpath(context.xml, context.xml)}]

    if xpaths1 and xpaths2:
        msg = fail_msg_both.format(xpath_expression1, xpath_expression2)
        if len(xpaths1) == len(xpaths2):
            zipped_xpaths = zip(xpaths1, xpaths2)
            for tup_xpath1, tup_xpath2 in zipped_xpaths:
                errors = [{
                    'message': msg,
                    'path': '{} & {}'.format(get_full_xpath(context.xml, tup_xpath1),
                                             get_full_xpath(context.xml, tup_xpath2))
                }]
        else:
            for xpath in xpaths2:
                errors.append({
                    'message': msg,
                    'path': '{} & {}'.format(get_full_xpath(context.xml, xpaths1[0]),
                                             get_full_xpath(context.xml, xpath))
                })
    return context, errors


@then('`{xpath_expression}` is not expected')
@register_ruleset_errors()
def step_not_expected(context, xpath_expression):
    errors = []

    for xpath in get_xpaths(context.xml, xpath_expression):
        errors.append({'message': '`{}` is not expected'.format(xpath_expression),
                       'path': get_full_xpath(context.xml, xpath)})
    return context, errors


@then('`{attribute}` start date attribute must be chronologically before end date attribute')
@register_ruleset_errors()
def step_start_date_before_end_date(context, attribute):
    xpath1 = get_xpaths(context.xml, context.xpath_expression1)
    xpath2 = get_xpaths(context.xml, context.xpath_expression2)
    errors = []

    if not xpath1 or not xpath2:
        return context, errors

    start_date_str = xpath1.attrib.get(attribute)
    end_date_str = xpath2.attrib.get(attribute)

    if not invalid_date_format(start_date_str) and not invalid_date_format(end_date_str):
        xpath1 = xpath1[0]
        xpath2 = xpath2[0]
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if start_date >= end_date:
            fail_msg = 'Start date ({}) must be before end date ({})'
            path_str1 = '{}/@{}'.format(get_full_xpath(context.xml, xpath1), attribute)
            path_str2 = '{}/@{}'.format(get_full_xpath(context.xml, xpath2), attribute)
            errors = [{
                'message': fail_msg.format(start_date_str, end_date_str),
                'path': '{} & {}'.format(path_str1, path_str2)
            }]
    return context, errors
