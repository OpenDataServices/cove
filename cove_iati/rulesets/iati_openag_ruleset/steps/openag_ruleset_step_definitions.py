'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
from behave import given, then

from cove_iati.lib.exceptions import RuleSetStepException


@given('an Open Agriculture IATI activity')
def step_given_iati_activity(context):
    assert True


@then('at least one `{xpath_expression}` is expected')
def step_openag_expected(context, xpath_expression):
    nsmap = context.xml.getparent().nsmap
    vals = context.xml.xpath(xpath_expression, namespaces=nsmap)
    if not vals:
        errors = [{
            'message': 'the activity should have at least one `{}`'.format(xpath_expression),
            'path': xpath_expression
        }]
        raise RuleSetStepException(context, errors)


@given('openag:tag elements')
def step_given_openag_tag(context):
    assert True


@then('at least one `{}` must use Agrovoc classification')
def step_openag_tag_with_agrovoc_classification(context, xpath_expression):
    nsmap = context.xml.getparent().nsmap
    values = context.xml.xpath(xpath_expression, namespaces=nsmap)
    fail = True

    if values:
        errors = []
        tree = context.xml.getroottree()
        for val in values:
            attributes = val.attrib
            attr_vocabulary = attributes.get('vocabulary') == '98' or attributes.get('vocabulary') == '99'
            attr_vocabulary_uri = attributes.get('vocabulary-uri') == 'http://aims.fao.org/aos/agrovoc/'
            attr_code = attributes.get('code')
            if attr_vocabulary and attr_vocabulary_uri and attr_code:
                fail = False
                break
        else:
            errors.append({
                'message': 'There should be at least one openag:tag using Agrovoc classification',
                'path': tree.getpath(val.getparent())
            })

        if fail:
            raise RuleSetStepException(context, errors)
