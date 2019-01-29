import json
from libcove.lib.exceptions import CoveInputDataError
from django.utils.translation import ugettext_lazy as _


class UnrecognisedFileTypeXML(CoveInputDataError):
    context = {
        'sub_title': _("Sorry, we can't process that data"),
        'link': 'index',
        'link_text': _('Try Again'),
        'msg': _('We did not recognise the file type.\n\nWe can only process xml, csv and xlsx files.')
    }


class RuleSetStepException(Exception):
    def __init__(self, context, errors=''):
        self.errors = errors
        self.id = ''
        self.feature_name = context.feature.name
        try:
            self.id = context.xml.xpath('iati-identifier/text()')[0]
        except IndexError:
            pass

    def __str__(self):
        return json.dumps({
            'errors': self.errors,
            'id': self.id,
            'ruleset': self.feature_name
        })
