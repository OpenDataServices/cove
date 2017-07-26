from django.utils.translation import ugettext_lazy as _

from cove.lib.exceptions import CoveInputDataError


def raise_invalid_version_argument(pk, version):
    raise CoveInputDataError(context={
        'sub_title': _("Something unexpected happened"),
        'link': 'explore',
        'link_args': pk,
        'link_text': _('Try Again'),
        'msg': _('We think you tried to run your data against an unrecognised version of '
                 'the schema.\n\n<span class="glyphicon glyphicon-exclamation-sign" '
                 'aria-hidden="true"></span> <strong>Error message:</strong> <em>{}</em> is '
                 'not a recognised choice for the schema version'.format(version)),
        'error': _('{} is not a valid schema version'.format(version))
    })


def raise_invalid_version_data_with_patch(version):
    raise CoveInputDataError(context={
        'sub_title': _("Version format does not comply with the schema"),
        'link': 'index',
        'link_text': _('Try Again'),
        'msg': _('The value for the <em>"version"</em> field in your data follows the '
                 '<em>major.minor.patch</em> pattern but according to the schema the patch digit '
                 'shouldn\'t be included (e.g. <em>"1.1.0"</em> should appear as <em>"1.1"</em> in '
                 'your data as the validator always uses the latest patch release for a major.minor '
                 'version).\n\nPlease get rid of the patch digit and try again.\n\n<span class="glyphicon '
                 'glyphicon-exclamation-sign" aria-hidden="true"></span> <strong>Error message: '
                 '</strong> <em>{}</em> format does not comply with the schema'.format(version)),
        'error': _('{} is not a valid schema version'.format(version))
    })
