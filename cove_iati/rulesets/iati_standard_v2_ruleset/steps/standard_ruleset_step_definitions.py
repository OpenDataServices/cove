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


@then('`{attribute}` attribute must be a valid date')
@register_ruleset_errors
def step_valid_date(context, attribute):
    xpaths = get_xpaths(context.xml, context.xpath_expression)
    errors = []

    if xpaths:
        for xpath in xpaths:
            date_str = xpath.attrib.get(attribute)
            if invalid_date_format(xpath, date_str):
                errors.append({'message': '`{}` is not a valid date'.format(date_str),
                               'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
    return context, errors


@then('`{attribute}` attribute must be today or in the past')
@register_ruleset_errors
def step_must_be_today_or_past(context, attribute):
    xpaths = get_xpaths(context.xml, context.xpath_expression)
    errors = []

    if xpaths:
        today = datetime.date.today()
        for xpath in xpaths:
            date_str = xpath.attrib.get(attribute)
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            if date > today:
                errors.append({'message': '{} must be on or before today ({})'.format(date, today),
                               'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
    return context, errors


@then('iati-identifier text should match the regex `{regex_str}`')
@register_ruleset_errors
def step_iati_id_text_match_regex(context, regex_str):
    xpath = get_xpaths(context.xml, context.xpath_expression)
    regex = re.compile(regex_str)
    errors = []

    if xpath:
        xpath = xpath[0]
        fail_msg = 'text does not match the regex {}'
        text_str = xpath.text
        if not regex.match(text_str):
            errors = [{'message': fail_msg.format(text_str, regex_str),
                       'path': '{}/text()'.format(get_full_xpath(context.xml, xpath))}]
    return context, errors


@then('`{attribute}` attribute should match the regex `{regex_str}`')
@register_ruleset_errors
def step_attribute_match_regex(context, attribute, regex_str):
    xpaths = get_xpaths(context.xml, context.xpath_expression)
    regex = re.compile(regex_str)
    errors = []

    if xpaths:
        fail_msg = '{} does not match the regex {}'
        for xpath in xpaths:
            attr_str = xpath.attrib.get(attribute)
            if not regex.match(attr_str):
                errors.append({'message': fail_msg.format(attr_str, regex_str),
                               'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
    return context, errors


@then('either `{xpath_expression1}` or `{xpath_expression2}` is expected')
@register_ruleset_errors
def step_either_or_expected(context, xpath_expression1, xpath_expression2):
    xpath = get_xpaths(context.xml, xpath_expression1) or get_xpaths(context.xml, xpath_expression2)
    errors = []

    if not xpath:
        fail_msg = 'Neither {} nor {} have been found'
        errors = [{'message': fail_msg.format(xpath_expression1, xpath_expression2),
                   'path': get_full_xpath(context.xml, context.xml)}]
    return context, errors


@then('`{xpath_expression}` is not expected')
@register_ruleset_errors
def step_should_not_be_present(context, xpath_expression):
    xpaths = get_xpaths(context.xml, xpath_expression)
    errors = []

    if xpaths:
        for xpath in xpaths:
            errors.append({'message': '`{}` is not expected'.format(xpath_expression),
                           'path': get_full_xpath(context.xml, xpath)})
    return context, errors


@then('both `{attribute}` attributes must be a valid date')
@register_ruleset_errors
def step_two_valid_dates(context, attribute):
    xpath1 = get_xpaths(context.xml, context.xpath_expression1)
    xpath2 = get_xpaths(context.xml, context.xpath_expression2)
    xpaths = []
    errors = []

    if xpath1:
        xpaths.append(xpath1[0])
    if xpath2:
        xpaths.append(xpath2[0])

    if xpaths:
        fail_msg = '`{}` is not a valid date'
        for xpath in xpaths:
            date_str = xpath.attrib.get(attribute)
            if invalid_date_format(xpath1, date_str):
                errors.append({'message': fail_msg.format(date_str),
                               'path': '{}/@{}'.format(get_full_xpath(context.xml, xpath), attribute)})
    return context, errors


@then('`{attribute}` start date attribute must be chronologically before end date attribute')
@register_ruleset_errors
def step_should_be_before(context, attribute):
    xpath1 = get_xpaths(context.xml, context.xpath_expression1)
    xpath2 = get_xpaths(context.xml, context.xpath_expression2)
    errors = []

    if not xpath1 or not xpath2:
        return context, errors

    xpath1 = xpath1[0]
    start_date_str = xpath1.attrib.get(attribute)
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    xpath2 = xpath2[0]
    end_date_str = xpath2.attrib.get(attribute)
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if start_date >= end_date:
        fail_msg = 'start date ({}) must be before end date ({})'
        path_str1 = '{}/@{}'.format(get_full_xpath(context.xml, xpath1), attribute)
        path_str2 = '{}/@{}'.format(get_full_xpath(context.xml, xpath2), attribute)
        errors = [{
            'message': fail_msg.format(start_date_str, end_date_str),
            'path': '{} & {}'.format(path_str1, path_str2)
        }]
    return context, errors
