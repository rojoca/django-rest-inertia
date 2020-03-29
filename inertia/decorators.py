import logging
from functools import wraps
from django.conf import settings
from rest_framework import response, views, viewsets, generics, exceptions

from .negotiation import InertiaObject, InertiaNegotiation, InertiaHTMLRenderer, InertiaJSONRenderer
from .exceptions import exception_handler

logger = logging.getLogger('inertia')



class AssetVersion(object):
    def get_version(self):
       return "test"


def inertia(component_path, template_name=None, **kwargs):
    def decorator(api_cls):
        class WrappedInertiaView(api_cls):
            content_negotiation_class = InertiaNegotiation
            inertia = None

            @property
            def default_response_headers(self):
                headers = super(WrappedInertiaView, self).default_response_headers
                headers["X-Inertia"] = True
                return headers

            def get_renderer_context(self):
                context = super(WrappedInertiaView, self).get_renderer_context()
                context["template_name"] = template_name  # TODO: or INERTIA_TEMPLATE_NAME
                context["inertia"] = self.inertia
                return context

            def get_exception_handler(self):
                return exception_handler

            def initialize_request(self, request, *args, **kwargs):
                request = super(WrappedInertiaView, self).initialize_request(request, *args, **kwargs)
                logger.debug(request.path)
                logger.debug(component_path)

                if not hasattr(request, 'inertia'):
                    # dynamically add InertiaObject to the request
                    request.inertia = InertiaObject.from_request(request, component_path)
                    self.inertia = request.inertia  # add to view as convenience

                return request

        return WrappedInertiaView
    return decorator


def component(component_path):
    """
    Sets the component for a method within a class based view.

    Can only be applied to methods inside APIView classes
    that return Response objects:

    ````
        class MyViewSet(ModelViewSet):
           # ...
           @component("My/Component")
           def retrieve(self, request, *args, **kwargs):
                # ...
                return Response(serializer.data)
    ````
    """
    def method_decorator(method):
        @wraps(method)
        def wrapper(*args, **kwargs):
            response = method(*args, **kwargs)

            if isinstance(response, response.Response):
                # monkey patch response
                response.component = component_path
            return response
        return wrapper
    return method_decorator

