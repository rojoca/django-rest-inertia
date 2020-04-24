import json
from django.test import TestCase
from django.db import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from drf_inertia.decorators import inertia, component
from drf_inertia.exceptions import set_error_redirect


class Action(models.Model):
    pass


class ErrorSerializer(serializers.Serializer):
    good_field = serializers.CharField(max_length=1000)
    bad_field = serializers.CharField(max_length=5)


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

    def test_decorated_api_view_handles_error(self):
        @inertia("Component/Path")
        class TestView(APIView):
            def get(self, request, **kwargs):
                raise ValidationError("This is an error")

        request = self.factory.get('/', HTTP_X_INERTIA=True)
        request.session = {}
        response = TestView.as_view()(request)
        assert response.status_code == 302
        assert "errors" in request.session
        assert response["Location"] == "/"

    def test_decorated_api_view_handles_serializer_error(self):
        @inertia("Component/Path")
        class TestView(APIView):
            def get(self, request, **kwargs):
                s = ErrorSerializer(data={"good_field": "test", "bad_field": "really long"})
                s.is_valid(raise_exception=True)

        request = self.factory.get('/', HTTP_X_INERTIA=True)
        request.session = {}
        response = TestView.as_view()(request)
        assert response.status_code == 302
        assert "errors" in request.session
        assert "bad_field" in request.session["errors"]
        assert response["Location"] == "/"

    def test_decorated_api_view_set_error_redirect(self):
        @inertia("Component/Path")
        class TestView(APIView):
            def get(self, request, **kwargs):
                set_error_redirect(request, "/error/redirect")
                raise ValidationError("This is an error")

        request = self.factory.get('/', HTTP_X_INERTIA=True)
        request.session = {}
        response = TestView.as_view()(request)
        assert response.status_code == 302
        assert "errors" in request.session
        assert response["Location"] == "/error/redirect"
