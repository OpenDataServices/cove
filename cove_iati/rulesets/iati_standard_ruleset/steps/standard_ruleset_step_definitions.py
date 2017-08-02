'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
from datetime import datetime
import json
import re

from behave import given, then

from cove_iati.lib.exceptions import RuleSetStepException


@given('an IATI activity')
def step_impl(context):
    # this is a dummy step. It's here because
    # behave / BDD requires at least one 'given' step.
    assert True


@then('`{xpath_expression}` should be present')
def step_should_be_present(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    if not vals:
        msg = '`{}` not found'.format(xpath_expression)
        raise RuleSetStepException(context, msg)


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
        msg = '{} {} not match the regex `{}`'.format(', '.join(bad_vals), verb, regex_str)
        raise RuleSetStepException(context, msg)


@given('`{xpath_expression}` is present')
def step_is_present(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    if vals:
        assert True
    else:
        msg = '`{}` is not present'.format(xpath_expression)
        raise RuleSetStepException(context, msg)


@then('`{xpath_expression}` should not be present')
def step_should_not_be_present(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    if not vals:
        assert True
    else:
        msg = '`{}` is present when it shouldn\'t be'.format(xpath_expression)
        raise RuleSetStepException(context, msg)


@given('`{xpath_expression}` is a valid date')
def step_valid_date(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    for val in vals:
        try:
            datetime.strptime(val, '%Y-%m-%d')
            assert True
            return
        except ValueError:
            msg = '"{}" is not a valid date'.format(val)
            raise RuleSetStepException(context, msg)
    msg = '`{}` not found'.format(xpath_expression)
    raise RuleSetStepException(context, msg)


@then('`{xpath_expression1}` should be chronologically before `{xpath_expression2}`')
def step_should_be_earlier(context, xpath_expression1, xpath_expression2):
    less_str = context.xml.xpath(xpath_expression1)[0]
    more_str = context.xml.xpath(xpath_expression2)[0]
    less = datetime.strptime(less_str, '%Y-%m-%d').date()
    more = datetime.strptime(more_str, '%Y-%m-%d').date()

    if less > more:
        msg = '{} should be before {}'.format(less_str, more_str)
        raise RuleSetStepException(context, msg)


@then('`{xpath_expression}` should be today, or in the past')
def step_should_be_past(context, xpath_expression):
    val = context.xml.xpath(xpath_expression)[0]
    date = datetime.strptime(val, '%Y-%m-%d').date()

    if date > context.today:
        msg = '{} should be on or before today ({})'.format(date, context.today)
        raise RuleSetStepException(context, msg)


@then('either `{xpath_expression1}` or `{xpath_expression2}` {statement}')
def step_either_or(context, xpath_expression1, xpath_expression2, statement):
    xpath_expressions = [xpath_expression1, xpath_expression2]
    tmpl = 'then `{{expression}}` {statement}'.format(statement=statement)
    exceptions = []

    for xpath_expression in xpath_expressions:
        try:
            context.execute_steps(tmpl.format(expression=xpath_expression))
            assert True
            return
        except AssertionError as e:
            msg = str(e).split('RuleSetStepException: ')[1]
            exceptions.append(msg)

    exception_messages = [json.loads(exception.strip())['message'] for exception in exceptions]
    msg = ' and '.join(exception_messages)
    raise RuleSetStepException(context, msg)
