import json
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.negotiation import DefaultContentNegotiation

from .config import VERSION, TEMPLATE_VAR
from .serializers import InertiaSerializer
from .exceptions import Conflict


class Inertia(object):
    is_data = False  # is the X-Inertia header present
    version = None
    component = None
    partial_data = None
    url = None
    data = {}

    def __init__(self, **kwargs):
        for k in kwargs:
            if hasattr(self, k):
                setattr(self, k, kwargs[k])

    def include(self, name):
        if not self.partial_data:
            return True

        return name in self.partial_data

    def __str__(self):
        return str(self.__dict__)

    def check_version(self):
        # if this is an X-Inertia: true request, and the versions match
        if self.is_data and self.version != VERSION:
            # this will trigger a refresh on the frontend
            # see https://inertiajs.com/the-protocol#asset-versioning
            raise Conflict()

    @classmethod
    def from_request(cls, request, component):
        inertia = Inertia()
        inertia.is_data = request.META.get('HTTP_X_INERTIA', False)
        inertia.component = component
        inertia.url = request.path
        inertia.version = request.META.get('HTTP_X_INERTIA_VERSION', None)

        if inertia.is_data:
            # if this is an X-Inertia: true request, check the version
            if inertia.version is not None and inertia.version != VERSION:
                raise Conflict()

            # set partial details if they exist and are valid
            partial_component = request.META.get('HTTP_X_INERTIA_PARTIAL_COMPONENT', None)
            partial_data = request.META.get('HTTP_X_INERTIA_PARTIAL_DATA', None)
            if partial_data and partial_component == component:
                inertia.partial_data = [s.strip() for s in partial_data.split(',')]

        return inertia


class InertiaRendererMixin(object):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # add the data to the inertia object then serialize it
        # with the InertiaSerializer
        renderer_context["request"].inertia.data = data
        serializer = InertiaSerializer(renderer_context["request"].inertia, context=renderer_context)
        data = serializer.data

        return super(InertiaRendererMixin, self).render(
            data, accepted_media_type=accepted_media_type, renderer_context=renderer_context)


class InertiaHTMLRenderer(InertiaRendererMixin, TemplateHTMLRenderer):
    def get_template_context(self, data, renderer_context):
        context = super(InertiaHTMLRenderer, self).get_template_context(data, renderer_context)

        # add the inertia data as json into the template
        context[TEMPLATE_VAR] = json.dumps(data)
        return context


class InertiaJSONRenderer(InertiaRendererMixin, JSONRenderer):
    pass


class InertiaNegotiation(DefaultContentNegotiation):

    def select_renderer(self, request, renderers, format_suffix=None):
        # check for inertia headers:
        if hasattr(request, 'inertia') and request.inertia.is_data:
            renderer = InertiaJSONRenderer()
            media_type = "application/json"
        else:
            # select the default renderer (could be JSON)
            # this allows calling the API without the inertia wrapper if necessary
            renderer, media_type = super(InertiaNegotiation, self).select_renderer(
                request, renderers, format_suffix=format_suffix)

            # once we have the renderer, check media_type and use the
            # inertia renderer if the media_type is html
            if "html" in media_type:
                renderer = InertiaHTMLRenderer()

        return (renderer, media_type)
