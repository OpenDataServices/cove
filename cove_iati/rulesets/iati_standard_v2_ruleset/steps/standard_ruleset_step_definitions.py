'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
import datetime
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


@then('`{attribute}` attribute must be a valid date')
def step_valid_date(context, attribute):
    xpaths = context.xml.xpath(context.xpath_expression)
    fail = False
    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        for xpath in xpaths:
            date_str = xpath.attrib.get(attribute)
            try:
                datetime.datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                errors.append({'message': '`{}` is not a valid date'.format(date_str),
                               'path': '{}/@{}'.format(tree.getpath(xpath), attribute)})
                fail = True
    if fail:
        raise RuleSetStepException(context, errors)


@then('`{attribute}` attribute must be today, or in the past')
def step_should_be_past(context, attribute):
    xpaths = context.xml.xpath(context.xpath_expression)
    fail = False

    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        today = datetime.date.today()
        for xpath in xpaths:
            date_str = xpath.attrib.get(attribute)
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            print(date)
            if date > today:
                errors.append({'message': '{} should be on or before today ({})'.format(date, today),
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


@then('either `{xpath_expression1}` or `{xpath_expression2}` should be present')
def step_should_be_present(context, xpath_expression1, xpath_expression2):
    vals = context.xml.xpath(xpath_expression1) or context.xml.xpath(xpath_expression2)
    if not vals:
        errors = [{
            'message': '`{}` and `{}` not found'.format(xpath_expression1, xpath_expression2),
            'path': ''
        }]
        raise RuleSetStepException(context, errors)
