import functools
import logging

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


class CoveInputDataError(Exception):
    """
    An error that we think is due to the data input by the user, rather than a
    bug in the application.
    """
    def __init__(self, context=None):
        if context:
            self.context = context


class UnrecognisedFileType(CoveInputDataError):
    context = {
        'sub_title': _("Sorry we can't process that data"),
        'link': 'index',
        'link_text': _('Try Again'),
        'msg': _('We did not recognise the file type.\n\nWe can only process json, csv and xlsx files.')
    }


class UnrecognisedFileTypeXML(CoveInputDataError):
    context = {
        'sub_title': _("Sorry we can't process that data"),
        'link': 'index',
        'link_text': _('Try Again'),
        'msg': _('We did not recognise the file type.\n\nWe can only process xml, csv and xlsx files.')
    }


def cove_web_input_error(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except CoveInputDataError as err:
            return render(request, 'error.html', context=err.context)
    return wrapper


def cove_spreadsheet_conversion_error(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except Exception as err:
            logger.exception(err, extra={
                'request': request,
                })
            raise CoveInputDataError({
                'sub_title': _("Sorry we can't process that data"),
                'link': 'index',
                'link_text': _('Try Again'),
                'msg': _('We think you tried to supply a spreadsheet, but we failed to convert it.'
                         '\n\nError message: {}'.format(repr(err)))
            })
    return wrapper
