from functools import wraps

from .negotiation import Inertia, InertiaNegotiation
from .exceptions import exception_handler
from .config import TEMPLATE


def inertia(component_path, template_name=None, **kwargs):
    """
    Decorator to apply to @api_views or class based views to convert the
    request into an interia request / response

    On function views (note the @api_view decorator is still required):

    @inertia("App/Dashboard)
    @api_view
    def get_dashboard_data(self, request, **kwargs):
        # ...
        return Response(data)


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
                             frontend for this view. For class based views or
                             viewsets this is the default component for all
                             methods.
    template_name (string):  Optional. override the default template used when
                             returning HTML
    **kwargs:                Any kwargs passed are used to map class based view
                             methods or viewset view methods to components e.g.
                             retrieve="Users/Detail" would ensure that the component
                             returned for the retrive method would be "Users/Detail"
    """
    def decorator(api_cls):
        class WrappedInertiaView(api_cls):
            content_negotiation_class = InertiaNegotiation
            inertia = None

            def get_component_path(self, request):
                """
                This method is to support setting different components for
                different methods in class based views or viewsets.

                e.g.

                @inertia("Users/List", retrieve="Users/Detail")
                class UserViewSet(viewsets.ViewSet):
                    # ...

                In this viewset, the retrieve method will use "Users/Detail" as
                the component path, while all other methods will use "Users/List"
                """
                if hasattr(self, "action"):
                    # viewsets set the "action" attribute on the instance
                    action = self.action
                else:
                    # class based views just use the HTTP method
                    action = request.method

                # if a kwarg is set for the action use it, otherwise use default
                return kwargs.get(action, component_path)

            @property
            def default_response_headers(self):
                headers = super(WrappedInertiaView, self).default_response_headers
                headers["X-Inertia"] = True
                return headers

            def get_renderer_context(self):
                context = super(WrappedInertiaView, self).get_renderer_context()
                context["template_name"] = TEMPLATE
                context["inertia"] = self.inertia
                return context

            def get_exception_handler(self):
                return exception_handler

            def initialize_request(self, request, *args, **kwargs):
                request = super(WrappedInertiaView, self).initialize_request(request, *args, **kwargs)

                if not hasattr(request, 'inertia'):
                    # dynamically add Inertia to the request
                    request.inertia = Inertia.from_request(request, self.get_component_path(request))
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

        return WrappedInertiaView
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
