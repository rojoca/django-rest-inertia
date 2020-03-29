import logging
import json
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError, APIException
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.negotiation import DefaultContentNegotiation
from .serializers import InertiaSerializer

logger = logging.getLogger('inertia')


def get_asset_version(request, is_data=False):
    """
    If an INERTIA_VERSION_CLASS has been set, then check
    the version against the requested version if the request
    is a GET request.
    """
    current_version = '0.0.1'
    requested_version = request.META.get('HTTP_X_INERTIA_VERSION', None)
    if is_data and hasattr(settings, 'INERTIA_VERSION_CLASS'):
        version_class = settings.INERTIA_ASSET_CLASS
        current_version = version_class().get_version()
        if current_version != version and request.method == 'get':
            raise Conflict()

    return current_version


class InertiaObject(object):
    is_data = False
    version = None
    component = None
    partial_data = None
    url = None
    data = {}

    def include(self, name):
        if not self.partial_data:
            return True

        return name in self.partial_data

    @classmethod
    def from_request(cls, request, component):
        inertia = InertiaObject()
        inertia.is_data = request.META.get('HTTP_X_INERTIA', False)
        inertia.component = component
        inertia.url = request.path
        inertia.version = get_asset_version(request, inertia.is_data)

        if inertia.is_data:
            # set partial details if they exist and are valid
            partial_component = request.META.get('HTTP_X_INERTIA_PARTIAL_COMPONENT', None)
            partial_data = request.META.get('HTTP_X_INERTIA_PARTIAL_DATA', None)
            if partial_data and partial_component == component:
                inertia.partial_data = [s.strip() for s in partial_data.split(',')]

        return inertia


class InertiaRendererMixin(object):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        try:
            logger.debug(renderer_context["request"].inertia.__dict__)
            # if there is a request with an inertia attribute
            # reformat the data with the InertiaSerializer
            renderer_context["request"].inertia.data = data
            serializer = InertiaSerializer(renderer_context["request"].inertia, context=renderer_context)
            data = serializer.data
            logger.debug(data)
        except (KeyError, AttributeError):
            logger.exception("InertiaRendererMixin.render")
            pass

        return super(InertiaRendererMixin, self).render(
            data, accepted_media_type=accepted_media_type, renderer_context=renderer_context)


class InertiaHTMLRenderer(InertiaRendererMixin, TemplateHTMLRenderer):
    def get_template_context(self, data, renderer_context):
        # allow data to be injected into template
        context = super(InertiaHTMLRenderer, self).get_template_context(data, renderer_context)
        context['json'] = json.dumps(data)
        return context

    def render(self, data, accepted_media_type=None, renderer_context=None):
        self.template_name = renderer_context.get("template_name") or 'index.html'
        return super(InertiaHTMLRenderer, self).render(
            data,
            accepted_media_type=accepted_media_type,
            renderer_context=renderer_context
        )


class InertiaJSONRenderer(InertiaRendererMixin, JSONRenderer):
    pass


class InertiaNegotiation(DefaultContentNegotiation):
    html_renderer = InertiaHTMLRenderer
    json_renderer = InertiaJSONRenderer

    def select_renderer(self, request, renderers, format_suffix=None):
        # check for inertia headers:
        if hasattr(request, 'inertia') and request.inertia.is_data:
            renderer = self.json_renderer()
            media_type = "application/json"
        else:
            renderer, media_type = super(InertiaNegotiation, self).select_renderer(
                request, renderers, format_suffix=format_suffix)

            # override the HTML renderer
            if media_type == "text/html":
                renderer = self.html_renderer()

        return (renderer, media_type)
