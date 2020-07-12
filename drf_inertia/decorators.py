from functools import wraps

from .negotiation import Inertia, InertiaNegotiation
from .exceptions import exception_handler
from .config import TEMPLATE, DEBUG


def inertia(component_path, template_name=None, **component_kwargs):
    """
    Decorator to apply to rest_framework views and viewsets to convert the
    request into an interia request / response

    Parameters:
    component_path (string): The component that should be passed back to the
                             frontend for this view. This is the default
                             component for all
                             methods.
    template_name (string):  Optional. override the default template used when
                             returning HTML
    **component_kwargs:      Any kwargs passed are used to map class based view
                             methods or viewset view methods to components e.g.
                             retrieve="Users/Detail" would ensure that the component
                             returned for the retrive method would be "Users/Detail"
    """
    def decorator(target):
        # if this is an api_view then there will be a cls property
        # otherwise just need to decorate the target
        cls = getattr(target, "cls", target)

        # need to keep the original initial method because we are
        # not extending cls, we are replacing the methods, so calling
        # super will not work as expected
        wrapped_initial = getattr(cls, "initial")

        def initial(self, request, *args, **kwargs):
            # Configure Inertia object and add to request
            if not hasattr(request, 'inertia'):
                # Get the action (~http method) to determine the component.
                # ViewSets set the "action" attribute on the instance,
                # class based views just use the HTTP method
                action = getattr(self, "action", request.method)
                cp = component_kwargs.get(action, component_path)

                request.inertia = Inertia.from_request(request, cp)
                self.inertia = request.inertia  # add to view as convenience

            # Asset Versioning:
            #
            # must do this after inertia has been added to the request
            # otherwise the exception handler will not have access to
            # the interia object (which will be on the request)
            request.inertia.check_version()

            # set the inertia template
            # this can still be overriden by get_template_names()
            if not hasattr(self, "template_name") or not self.template_name:
                self.template_name = template_name or TEMPLATE

            # call the wrapped initial method
            wrapped_initial(self, request, *args, **kwargs)

        def raise_uncaught_exception(self, exc):
            if DEBUG:
                request = self.request
                request.accepted_renderer = 'html'
                request.accepted_media_type = "text/html"
            raise exc

        # add the updated methods to the cls
        cls.get_content_negotiator = lambda self: InertiaNegotiation()
        cls.get_exception_handler = lambda self: exception_handler
        cls.initial = initial
        cls.raise_uncaught_exception = raise_uncaught_exception
        return target
    return decorator


def component(component_path):
    """
    Sets the component for a method within a class based view.

    Can only be applied to methods inside APIView classes or ViewSets

    This is a convenience decorator to locate the inertia component
    path close to the method it is used with in viewsets or class
    based views, instead of specifying all the component paths at
    the top of the class.

    The @inertia decorator is still required on the class.

    The @component decorator will always override components set in
    the inertia decorator.
    ```
        # the following:
        @inertia("Users/List", retrieve="Users/Detail")
        class UserViewSet(ModelViewSet):
            # ...

        # is equivalent to:

        @inertia("Users/List")
        class UserViewSet(ModelViewSet):
           # ...
           @component("Users/Detail")
           def retrieve(self, request, *args, **kwargs):
                # ...
                return Response(serializer.data)
    ```
    """
    def method_decorator(method):
        @wraps(method)
        def wrapper(*args, **kwargs):
            # update the request inertia object if it exists
            if args[1] and hasattr(args[1], "inertia"):
                args[1].inertia.component = component_path
            return method(*args, **kwargs)
        return wrapper
    return method_decorator
