from django.urls import reverse
from django.utils.module_loading import import_string
from rest_framework import status, views
from rest_framework.exceptions import ValidationError, APIException, PermissionDenied, NotAuthenticated

from .config import EXCEPTION_HANDLER, AUTH_REDIRECT, AUTH_REDIRECT_URL_NAME


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Asset version conflict.'
    default_code = 'conflict'

    def __init__(self, detail=None, code=None, available_renderers=None):
        self.available_renderers = available_renderers
        super().__init__(detail, code)


class DefaultExceptionHandler(object):

    def get_redirect_status(self, request):
        if request.method.lower() in ["put", "patch", "delete"]:
            return status.HTTP_303_SEE_OTHER

        return status.HTTP_302_FOUND

    def get_auth_redirect(self):
        if AUTH_REDIRECT_URL_NAME:
            return reverse(AUTH_REDIRECT_URL_NAME)

        return AUTH_REDIRECT

    def handle(self, exc, context):
        override_status = None
        override_headers = {}

        request = context["request"]
        is_inertia = hasattr(request, "inertia")

        if is_inertia and isinstance(exc, ValidationError):
            # redirect user to the error redirect for this page (default is current page)
            override_headers["Location"] = request.inertia.get_error_redirect(request)
            override_status = self.get_redirect_status(request)

        if is_inertia and (isinstance(exc, PermissionDenied) or isinstance(exc, NotAuthenticated)):
            # redirect to the AUTH_REDIRECT
            override_status = self.get_redirect_status(request)
            override_headers["Location"] = self.get_auth_redirect()

        # use rest framework exception handler to get the response
        # this will only catch APIException, 404, or PermissionDenied
        response = views.exception_handler(exc, context)

        if not response:
            # If here there is an unintended exception (e.g. syntax error) and
            # django should handle it.
            return

        if override_status:
            response.status_code = override_status
            if response.data:
                # add the errors to the users session
                request.session["errors"] = response.data

        if is_inertia and response.status_code == status.HTTP_409_CONFLICT:
            response['X-Inertia-Location'] = request.path

        for header in override_headers:
            response[header] = override_headers[header]

        return response


def exception_handler(exc, context):
    handler = import_string(EXCEPTION_HANDLER)
    return handler().handle(exc, context)


def set_error_redirect(request, error_redirect):
    """
    Convenience method to set the Location redirected
    to after an error. Should be used at the top of
    views.

    You could call set_error_redirect on the interia
    object directly but you need to check that the
    inertia object is actually there.
    """
    if hasattr(request, "inertia"):
        request.inertia.set_error_redirect(error_redirect)
