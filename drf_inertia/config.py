from django.conf import settings


# the version to use for ASSET VERSIONING
VERSION = getattr(settings, "INERTIA_VERSION", "unversioned")

# the HTML template for interia requests (can be overridden by the @intertia decorator)
TEMPLATE = getattr(settings, 'INERTIA_HTML_TEMPLATE', 'index.html')

# the django template var the inertia json should be set to
TEMPLATE_VAR = getattr(settings, 'INERTIA_TEMPLATE_VAR', 'inertia_json')

SHARED_DATA_SERIALIZER = getattr(settings, 'INERTIA_SHARED_SERIALIZER', 'drf_inertia.serializers.DefaultSharedSerializer')

# The exception handler for inertia requests
# ensures that exceptions are returned in interia
# format
EXCEPTION_HANDLER = getattr(settings, 'INERTIA_EXCEPTION_HANDLER', 'drf_inertia.exceptions.DefaultExceptionHandler')

# The auth redirect is used in the default exception handler
# to determine where to go when 401 or 403 errors are raised
AUTH_REDIRECT = getattr(settings, 'INERTIA_AUTH_REDIRECT', '/login')

# if AUTH_REDIRECT_URL_NAME is specified use django.urls.reverse
# to get the AUTH_REDIRECT instead
AUTH_REDIRECT_URL_NAME = getattr(settings, 'INERTIA_AUTH_REDIRECT_URL_NAME', None)
