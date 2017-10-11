from behave import then

from cove.lib.common import get_orgids_prefixes
from cove_iati.rulesets.utils import get_child_full_xpath, get_xobjects, register_ruleset_errors

ORGIDS_PREFIXES = get_orgids_prefixes()


@then('`{attribute}` id attribute must start with an org-ids prefix')
@register_ruleset_errors()
def step_openag_org_id_prefix_expected(context, attribute):
    errors = []
    fail_msg = '@{} {} does not start with a recognised org-ids prefix'

    for xpath in get_xobjects(context.xml, context.xpath_expression):
        attr_id = xpath.attrib.get(attribute, '')
        for prefix in ORGIDS_PREFIXES:
            if attr_id.startswith(prefix):
                break
        else:
            errors.append({'message': fail_msg.format(attribute, attr_id),
                           'path': '{}/@{}'.format(get_child_full_xpath(context.xml, xpath), attribute)})
    return context, errors
