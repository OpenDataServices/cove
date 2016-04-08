# How Cove deals with errors

Errors in Cove can be broken down into 2 categories:
* Deliberately caught errors - to some extent we're expecting something to go wrong, probably due to people's data
* Uncaught 500 errors - something unexpected breaks

Breaking these down further:
* Deliberately caught errors
    * Custom message - something's wrong with the data, and we know what, so are able to display some custom help text. Since we know this is a data problem, it doesn't get logged in Sentry.
    * Generic message - something went wrong that we think is very likely to be a data issue (e.g. conversion failed), but we don't have a custom error message for it. We show the user the caught error, but also log it to Sentry.
* Uncaught 500 errors
    * Themed 500 error page - an otherwise uncaught exception, but we successfully rendered the friendly, well themed 500 page. These are always reported to Sentry.
    * Unthemed 500 error page - something went very wrong and we couldn't even display the nice 500 error page. The error should be reported to Sentry, but that may be broken too! In general these are serious bugs, and should be reported.

In an ideal world we want to eliminate all error messages except for the custom ones (ie. the only errors are data errors, and we can tell the users how to fix them).

