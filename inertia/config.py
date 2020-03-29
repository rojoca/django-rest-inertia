from django.conf import settings


EXCEPTION_HANDLER = getattr(settings, 'INERTIA_EXCEPTION_HANDLER', 'inertia.exceptions.DefaultExceptionHandler')
AUTH_REDIRECT = getattr(settings, 'INERTIA_AUTH_REDIRECT', '/login')
AUTH_REDIRECT_URL_NAME = getattr(settings, 'INERTIA_AUTH_REDIRECT_URL_NAME', None)
