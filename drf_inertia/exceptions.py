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
            # add the errors to the users sessiong
            request.session["errors"] = exc.detail

            # redirect back to the requested page
            override_headers["Location"] = request.path
            override_status = status.HTTP_302_FOUND

        if is_inertia and (isinstance(exc, PermissionDenied) or isinstance(exc, NotAuthenticated)):
            # redirect to the AUTH_REDIRECT
            override_status = status.HTTP_302_FOUND
            override_headers["Location"] = self.get_auth_redirect()

        # use rest framework exception handler to get the response
        response = views.exception_handler(exc, context)

        if override_status:
            response.status_code = override_status

        if is_inertia and response.status_code == status.HTTP_409_CONFLICT:
            response['X-Inertia-Location'] = request.path

        for header in override_headers:
            response[header] = override_headers[header]

        return response


def exception_handler(exc, context):
    handler = import_string(EXCEPTION_HANDLER)
    handler().handle(exc, context)
