import functools

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _


class CoveInputDataError(Exception):
    """
    An error that we think is due to the data input by the user, rather than a
    bug in the application.
    """
    def __init__(self, context=None):
        if context:
            self.context = context


class CoveWebInputDataError(CoveInputDataError):
    """
    An error that we think is due to the data input by the user, rather than a
    bug in the application. Returns nicely rendered HTML. Depends on Django
    """
    def __init__(self, context=None):
        if context:
            self.context = context

    @staticmethod
    def error_page(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                return func(request, *args, **kwargs)
            except CoveInputDataError as err:
                return render(request, 'error.html', context=err.context)
        return wrapper


class UnrecognisedFileType(CoveInputDataError):
    context = {
        'sub_title': _("Sorry we can't process that data"),
        'link': 'cove:index',
        'link_text': _('Try Again'),
        'msg': _('We did not recognise the file type.\n\nWe can only process json, csv and xlsx files.')
    }
