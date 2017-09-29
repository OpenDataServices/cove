'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
import datetime
import re

from behave import given, then

from cove_iati.lib.exceptions import RuleSetStepException


def invalid_date_format(xpath, date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return True
    return False


@given('an IATI activity')
def step_given_iati_activity(context):
    assert True


@given('`{xpath_expression}` organisations')
def step_given_organisations(context, xpath_expression):
    context.xpath_expression = xpath_expression


@given('`{xpath_expression}` elements')
def step_given_elements(context, xpath_expression):
    context.xpath_expression = xpath_expression


@given('`{xpath_expression}` texts')
def step_given_texts(context, xpath_expression):
    context.xpath_expression = xpath_expression


@given('`{xpath_expression1}` plus `{xpath_expression2}`')
def step_given_two_different_elements(context, xpath_expression1, xpath_expression2):
    context.xpath_expression1 = xpath_expression1
    context.xpath_expression2 = xpath_expression2


@then('`{attribute}` attribute must be a valid date')
def step_valid_date(context, attribute):
    xpaths = context.xml.xpath(context.xpath_expression)
    fail = False

    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        for xpath in xpaths:
            date_str = xpath.attrib.get(attribute)
            if invalid_date_format(xpath, date_str):
                errors.append({'message': '`{}` is not a valid date'.format(date_str),
                               'path': '{}/@{}'.format(tree.getpath(xpath), attribute)})
                fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('`{attribute}` attribute must be today, or in the past')
def step_must_be_today_or_past(context, attribute):
    xpaths = context.xml.xpath(context.xpath_expression)
    fail = False

    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        today = datetime.date.today()
        for xpath in xpaths:
            date_str = xpath.attrib.get(attribute)
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            if date > today:
                errors.append({'message': '{} must be on or before today ({})'.format(date, today),
                               'path': '{}/@{}'.format(tree.getpath(xpath), attribute)})
                fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('every `{xpath_expression}` should match the regex `{regex_str}`')
def step_match_regex(context, xpath_expression, regex_str):
    vals = context.xml.xpath(xpath_expression)
    regex = re.compile(regex_str)
    success = True
    bad_vals = []

    for val in vals:
        if not regex.match(val):
            success = False
            bad_vals.append(val)
    if not success:
        verb = 'does' if len(bad_vals) == 1 else 'do'
        errors = [{
            'message': '{} {} not match the regex `{}`'.format(', '.join(bad_vals), verb, regex_str),
            'path': xpath_expression
        }]
        raise RuleSetStepException(context, errors)


@then('`{xpath_expression}` should not be present')
def step_should_not_be_present(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    if vals:
        errors = [{
            'message': '`{}` is present when it shouldn\'t be'.format(xpath_expression),
            'path': xpath_expression
        }]
        raise RuleSetStepException(context, errors)


@then('both `{attribute}` attributes must be a valid date')
def step_two_valid_dates(context, attribute):
    xpath1 = context.xml.xpath(context.xpath_expression1)
    xpath2 = context.xml.xpath(context.xpath_expression1)
    xpaths = []
    fail = False
    if xpath1:
        xpaths.append(xpath1[0])
    if xpath2:
        xpaths.append(xpath2[0])

    if xpaths:
        fail_msg = '`{}` is not a valid date'
        errors = []
        tree = context.xml.getroottree()
        for xpath in xpaths:
            date_str = xpath.attrib.get(attribute)
            if invalid_date_format(xpath1, date_str):
                errors.append({'message': fail_msg.format(date_str),
                               'path': '{}/@{}'.format(tree.getpath(xpath), attribute)})
                fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('`{attribute}` start date attribute must be chronologically before end date attribute')
def step_should_be_before(context, attribute):
    xpath1 = context.xml.xpath(context.xpath_expression1)
    xpath2 = context.xml.xpath(context.xpath_expression2)
    if not xpath1 or not xpath2:
        return

    xpath1 = xpath1[0]
    start_date_str = xpath1.attrib.get(attribute)
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    xpath2 = xpath2[0]
    end_date_str = xpath2.attrib.get(attribute)
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    fail_msg = 'start date ({}) must be before end date ({})'

    if start_date >= end_date:
        tree = context.xml.getroottree()
        path_str1 = '{}/@{}'.format(tree.getpath(xpath1), attribute)
        path_str2 = '{}/@{}'.format(tree.getpath(xpath2), attribute)
        errors = [{
            'message': fail_msg.format(start_date_str, end_date_str),
            'path': '{} & {}'.format(path_str1, path_str2)
        }]
        raise RuleSetStepException(context, errors)


@then('either `{xpath_expression1}` or `{xpath_expression2}` should be present')
def step_should_be_present(context, xpath_expression1, xpath_expression2):
    vals = context.xml.xpath(xpath_expression1) or context.xml.xpath(xpath_expression2)
    if not vals:
        errors = [{
            'message': '`{}` and `{}` not found'.format(xpath_expression1, xpath_expression2),
            'path': ''
        }]
        raise RuleSetStepException(context, errors)
