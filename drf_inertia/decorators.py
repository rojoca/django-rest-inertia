from functools import wraps

from .negotiation import Inertia, InertiaNegotiation
from .exceptions import exception_handler
from .config import TEMPLATE


def inertia(component_path, template_name=None, **component_kwargs):
    """
    Decorator to apply to class based views to convert the
    request into an interia request / response

    On class based views:

    @inertia("App/Dashboard)
    class DashboardView(APIView):
        def get(self, request, **kwargs):
            # ...
            return Response(data)

    On viewsets:

    @inertia("Users/List", retrieve="Users/Detail")
    class UserViewSet(viewsets.ViewSet):
        def list(self, request):
            # ...
            serializer = UserSerializer(queryset, many=True)
            return Response(serializer.data)

        def retrieve(self, request, pk=None):
            # ...
            serializer = UserSerializer(user)
            return Response(serializer.data)


    Parameters:
    component_path (string): The component that should be passed back to the
                             frontend for this view. This is the default
                             component for all
                             methods.
    template_name (string):  Optional. override the default template used when
                             returning HTML
    **kwargs:                Any kwargs passed are used to map class based view
                             methods or viewset view methods to components e.g.
                             retrieve="Users/Detail" would ensure that the component
                             returned for the retrive method would be "Users/Detail"
    """
    def decorator(target):
        # if this is an api_view then there will be a cls property
        # otherwise just need to decorate the target
        cls = getattr(target, "cls", target)

        # need to keep the original initialize_request because we are
        # not extending cls, we are replacing the methods, so calling
        # super will not work as expected
        wrapped_initialize_request = getattr(cls, "initialize_request")

        def initialize_request(self, request, *args, **kwargs):
            request = wrapped_initialize_request(self, request, *args, **kwargs)

            if not hasattr(request, 'inertia'):
                # get the action (~htp method) to determine the component
                if hasattr(self, "action"):
                    # viewsets set the "action" attribute on the instance
                    action = self.action
                else:
                    # class based views just use the HTTP method
                    action = request.method

                # if a kwarg is set for the action use it, otherwise use default
                request.inertia = Inertia.from_request(request, component_kwargs.get(action, component_path))
                self.inertia = request.inertia  # add to view as convenience

            # Asset Versioning:
            #
            # must do this after inertia has been added to the request
            # otherwise the exception handler will not have access to
            # the interia object (which will be on the request)
            request.inertia.check_version()

            # set the inertia template
            # this can still be overriden by get_template_names()
            self.template_name = template_name or TEMPLATE

            return request

        # add the updated methods to the cls
        cls.get_content_negotiator = lambda self: InertiaNegotiation()
        cls.get_exception_handler = lambda self: exception_handler
        cls.initialize_request = initialize_request
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
