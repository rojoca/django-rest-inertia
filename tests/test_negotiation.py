import pytest
from django.http import Http404
from django.test import TestCase

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.utils.mediatypes import _MediaType

from drf_inertia.negotiation import Inertia, InertiaNegotiation, InertiaJSONRenderer, InertiaHTMLRenderer

factory = APIRequestFactory()


class MockInertia(Inertia):
    is_data = True
    component = "Test/Component"
    url = "/"
    version = "unversioned"


class TestInertia(TestCase):
    def test_from_request_is_data_true(self):
        request = Request(factory.get('/', HTTP_X_INERTIA=True))
        inertia = Inertia.from_request(request, "Component/Path")
        assert inertia.is_data
        assert inertia.component == "Component/Path"
        assert inertia.url == "/"

    def test_from_request_is_data_false(self):
        request = Request(factory.get('/'))
        inertia = Inertia.from_request(request, "Component/Path")
        assert inertia.is_data is False

    def test_from_request_partial_data(self):
        component = "Component/Path"
        request = Request(factory.get(
            '/',
            HTTP_X_INERTIA=True,
            HTTP_X_INERTIA_PARTIAL_DATA='prop1,prop2',
            HTTP_X_INERTIA_PARTIAL_COMPONENT=component))
        inertia = Inertia.from_request(request, component)
        assert inertia.is_data
        assert inertia.partial_data == ['prop1', 'prop2']


class TestInertiaNegotiation(TestCase):
    def setUp(self):
        self.negotiator = InertiaNegotiation()

    def select_renderer(self, request):
        return self.negotiator.select_renderer(request, self.renderers)

    def test_inertia_request_selects_json_renderer(self):
        request = Request(factory.get('/'))
        request.inertia = Inertia()


