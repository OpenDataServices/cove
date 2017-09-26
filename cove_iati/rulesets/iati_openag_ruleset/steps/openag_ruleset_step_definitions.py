'''
Adapted from https://github.com/pwyf/bdd-tester/blob/master/steps/standard_ruleset_step_definitions.py
Released under MIT License
License: https://github.com/pwyf/bdd-tester/blob/master/LICENSE
'''
from behave import given, then

from cove_iati.lib.exceptions import RuleSetStepException


def get_xpaths(context, xpath_expression):
    nsmap = context.xml.getparent().nsmap
    xpaths = context.xml.xpath(xpath_expression, namespaces=nsmap)
    return xpaths


@given('an Open Agriculture IATI activity')
def step_given_iati_activity(context):
    assert True


@then('at least one `{xpath_expression}` is expected')
def step_openag_expected(context, xpath_expression):
    xpaths = get_xpaths(context, xpath_expression)
    if not xpaths:
        tree = context.xml.getroottree()
        errors = [{
            'message': 'the activity should include at least one {} element'.format(xpath_expression),
            'path': tree.getpath(context.xml)
        }]
        raise RuleSetStepException(context, errors)


@given('openag:tag elements')
def step_given_openag_tag(context):
    assert True


@then('every `{xpath_expression}` must have @vocabulary="98"|"99"')
def step_openag_tag_vocabulary(context, xpath_expression):
    xpaths = get_xpaths(context, xpath_expression)
    fail = False

    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        for xpath in xpaths:
            attrib = xpath.attrib
            vocabulary = attrib.get('vocabulary')
            org_vocabulary = attrib.get('vocabulary') == '98' or attrib.get('vocabulary') == '99'

            if vocabulary and org_vocabulary:
                continue
            else:
                if not vocabulary:
                    msg = '{} element must have a vocabulary attribute'.format(xpath_expression)
                elif not org_vocabulary:
                    msg = '{} element must have code "98" or "99" for the vocabulary attribute (it is "{}")'
                    msg = msg.format(xpath_expression, attrib.get('vocabulary'))

                errors.append({'message': msg, 'path': tree.getpath(xpath)})
                fail = True

    if fail:
        raise RuleSetStepException(context, errors)


@then('every `{xpath_expression}` must have @vocabulary-uri=="http://aims.fao.org/aos/agrovoc/"')
def step_openag_tag_vocabulary_uri(context, xpath_expression):
    xpaths = get_xpaths(context, xpath_expression)
    fail = False

    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        for xpath in xpaths:
            attrib = xpath.attrib
            vocabulary_uri = attrib.get('vocabulary-uri')
            agrovoc_uri = attrib.get('vocabulary-uri') == 'http://aims.fao.org/aos/agrovoc/'

            if vocabulary_uri and agrovoc_uri:
                continue
            else:
                if not vocabulary_uri:
                    msg = '{} element must have a vocabulary-uri attribute'.format(xpath_expression)
                elif not agrovoc_uri:
                    msg = ('{} element must have "http://aims.fao.org/aos/agrovoc/" '
                           'uri for the vocabulary-uri attribute (it is "{}")')
                    msg = msg.format(xpath_expression, attrib.get('vocabulary-uri'))

                errors.append({'message': msg, 'path': tree.getpath(xpath)})
                fail = True

    if fail:
        raise RuleSetStepException(context, errors)


@then('every `{xpath_expression}` must have @code')
def step_openag_tag_code(context, xpath_expression):
    xpaths = get_xpaths(context, xpath_expression)
    fail = False

    if xpaths:
        errors = []
        tree = context.xml.getroottree()
        for xpath in xpaths:
            attrib = xpath.attrib
            code_attrib = attrib.get('code')

            if code_attrib:
                continue
            else:
                if not code_attrib:
                    msg = '{} element must have a code attribute'.format(xpath_expression)
                    errors.append({'message': msg, 'path': tree.getpath(xpath)})
                    fail = True

    if fail:
        raise RuleSetStepException(context, errors)
