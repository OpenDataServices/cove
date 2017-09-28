'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
from datetime import datetime
import re

from behave import given, then

from cove_iati.lib.exceptions import RuleSetStepException


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


@given('`{xpath_expression}` is a valid date')
def step_given_date(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    errors = []
    if not vals:
        errors.append({
            'message': '`{}` not found'.format(xpath_expression),
            'path': xpath_expression
        })
        raise RuleSetStepException(context, errors)

    for val in vals:
        try:
            datetime.strptime(val, '%Y-%m-%d')
        except ValueError:
            errors = [{
                'messsage': '`{}` is not a valid date'.format(val),
                'path': xpath_expression
            }]
            raise RuleSetStepException(context, errors)


@given('`{xpath_expression}` is a valid date')
def step_given_date(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    errors = []
    if not vals:
        errors.append({
            'message': '`{}` not found'.format(xpath_expression),
            'path': xpath_expression
        })
        raise RuleSetStepException(context, errors)

    for val in vals:
        try:
            datetime.strptime(val, '%Y-%m-%d')
        except ValueError:
            errors = [{
                'messsage': '`{}` is not a valid date'.format(val),
                'path': xpath_expression
            }]
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



@then('`{xpath_expression1}` should be chronologically before `{xpath_expression2}`')
def step_should_be_before(context, xpath_expression1, xpath_expression2):
    less_str = context.xml.xpath(xpath_expression1)[0]
    more_str = context.xml.xpath(xpath_expression2)[0]
    less = datetime.strptime(less_str, '%Y-%m-%d').date()
    more = datetime.strptime(more_str, '%Y-%m-%d').date()

    if less > more:
        errors = [{
            'message': '{} should be before {}'.format(less_str, more_str),
            'path': ''
        }]
        raise RuleSetStepException(context, errors)


@then('`{xpath_expression}` should be today, or in the past')
def step_should_be_past(context, xpath_expression):
    values = context.xml.xpath(xpath_expression)
    fail = False

    if values:
        errors = []
        tree = context.xml.getroottree()
        for val in values:
            date = datetime.strptime(val, '%Y-%m-%d').date()
            if date > context.today:
                errors.append({
                    'message': '{} should be on or before today ({})'.format(date, context.today),
                    'path': tree.getpath(val.getparent())
                })
                fail = True

    if fail:
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
