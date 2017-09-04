from django.utils.translation import ugettext_lazy as _

from cove.lib.exceptions import CoveInputDataError


def raise_invalid_version_argument(pk, version):
    raise CoveInputDataError(context={
        'sub_title': _('Unrecognised version of the schema'),
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
        'sub_title': _('Version format does not comply with the schema'),
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


def raise_json_deref_error(pk, error):
    raise CoveInputDataError(context={
        'sub_title': _('JSON reference error'),
        'link': 'explore',
        'link_args': pk,
        'link_text': _('Try Again'),
        'msg': _('We have detected a JSON reference error in the schema. This <em> may be '
                 '</em> due to some extension trying to resolve non-existing references. '
                 '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                 '</span> <strong>Error message:</strong> <em>{}</em>'.format(error)),
        'error': _('{}'.format(error))
    })


def raise_missing_package_error(pk):
    raise CoveInputDataError(context={
        'sub_title': _('Missing OCDS package'),
        'link': 'explore',
        'link_args': pk,
        'link_text': _('Try Again'),
        'msg': _('Your data is not in the right package format (either <em>release-package'
                 '</em> or <em> record-package</em>). Please keep in mind that OCDS releases '
                 'are intended to be published within a package.\n\nIf you are trying to '
                 'validate a single release you can add it to the <code>"releases"</code> '
                 'field in a release-package.\n\n<span class="glyphicon glyphicon-exclamation-'
                 'sign" aria-hidden="true"></span> <strong>Error message:</strong> <em>'
                 'Missing OCDS package</em>'),
        'error': _('Missing OCDS package')
    })
