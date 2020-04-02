import json
from django.test import TestCase
from django.db import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from drf_inertia.decorators import inertia, component


class Action(models.Model):
    pass


class DecoratorTestCase(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    def _finalize_response(self, request, response, *args, **kwargs):
        response.request = request
        return APIView.finalize_response(self, request, response, *args, **kwargs)

    def test_api_view_decorated(self):
        """
        Ensure adding inertia decorator to api_view works
        """
        @inertia("Component/Path")
        @api_view(["GET"])
        def view(request):
            return Response(data={})

        request = self.factory.get('/', HTTP_X_INERTIA=True)
        response = view(request)
        data = json.loads(response.rendered_content)
        assert "component" in data
        assert "props" in data
        assert "url" in data
        assert "version" in data
        assert data["component"] == "Component/Path"
        assert response.status_code == 200
        assert response['Content-Type'] == "application/json"

    def test_api_view_class_decorated(self):
        @inertia("Component/Path")
        class TestView(APIView):
            def get(self, request, **kwargs):
                return Response(data={})

        request = self.factory.get('/', HTTP_X_INERTIA=True)
        response = TestView.as_view()(request)
        data = json.loads(response.rendered_content)
        assert "component" in data
        assert "props" in data
        assert "url" in data
        assert "version" in data
        assert data["component"] == "Component/Path"
        assert response.status_code == 200
        assert response['Content-Type'] == "application/json"

    def test_component_method_decorated(self):
        @inertia("Component/Path")
        class TestView(APIView):
            @component("Component/Other")
            def get(self, request, **kwargs):
                return Response(data={})

        request = self.factory.get('/', HTTP_X_INERTIA=True)
        response = TestView.as_view()(request)
        data = json.loads(response.rendered_content)
        assert "component" in data
        assert "props" in data
        assert "url" in data
        assert "version" in data
        assert data["component"] == "Component/Other"
        assert response.status_code == 200
        assert response['Content-Type'] == "application/json"

    def test_viewset_decorated(self):
        @inertia("Action/List")
        class ActionViewSet(GenericViewSet):
            queryset = Action.objects.all()

            def list(self, request, *args, **kwargs):
                response = Response(data={"view": "list"})
                return response

        request = self.factory.get('/', HTTP_X_INERTIA=True)
        response = ActionViewSet.as_view({'get': 'list'})(request)
        data = json.loads(response.rendered_content)
        assert "component" in data
        assert "props" in data
        assert "url" in data
        assert "version" in data
        assert data["component"] == "Action/List"
        assert data["props"]["view"] == "list"
        assert response.status_code == 200
        assert response['Content-Type'] == "application/json"
