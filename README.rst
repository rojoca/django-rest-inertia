django-rest-inertia
======================================

|build-status-image| |pypi-version|

Overview
--------

A django rest framework adapter for Inertia https://inertiajs.com/

Requirements
------------

-  Python (2.7, 3.3+)
-  Django (1.11, 2.2, 3.0)
-  Django REST Framework (2.4, 3.0, 3.1)

Installation
------------

Install using ``pip``\ …

.. code:: bash

    $ pip install django-rest-inertia

Example
-------

To use django-inertia-rest, decorate your views with the ``@inertia`` decorator
passing it the frontend component:

.. code:: python

    from rest_framework import views, viewsets
    from rest_framework.response import Response
    from rest_framework.decorators import api_view

    from drf_inertia.decorators import inertia

    # on a function based view:
    @inertia("User/List")
    @api_view(["GET"])
    def get_users(request,  **kwargs):
        return Response(data={"users": []})

    # on a class based view:
    @inertia("User/List")
    class UsersView(views.APIView):
        def get(self, request, **kwargs):
            return Response(data={"users": []})

Both these views would return the following:

.. code:: HTTP

    GET: http://example.com/users
    Accept: text/html, application/xhtml+xml
    X-Inertia: true
    X-Inertia-Version: unversioned

    HTTP/1.1 200 OK
    Content-Type: application/json

    {
      "component": "User/List",
      "props": {
        "users": []
      },
      "url": "/users",
      "version": "unversioned"
    }

Note that if you make a request to the API without the ``X-Inertia``
headers and using an ``Accept`` header that does not include html,
then you will get a response as though there is no ``@inertia``
decorator:

.. code:: HTTP

    GET: http://example.com/users
    Accept: application/json

    HTTP/1.1 200 OK
    Content-Type: application/json

    {
      "users": []
    }


For ViewSets, each action may need a different component:

.. code:: python

    # on a viewset:
    @inertia("User/List", retrieve="Users/Detail")
    class UserViewSet(viewsets.ModelViewSet):
        queryset = User.objects.all()

Or you can use the ``@component`` decorator:

.. code:: python

    from drf_inertia.decorators import inertia, component
    
    @inertia("User/List")
    class UserViewSet(viewsets.ModelViewSet):
        queryset = User.objects.all()

        @component("User/Detail")
        def retrieve(self, request, pk=None):
            //...
            return Response(data=user_data)

Testing
-------

Install testing requirements.

.. code:: bash

    $ pip install -r requirements.txt

Run with runtests.

.. code:: bash

    $ ./runtests.py

You can also use the excellent `tox`_ testing tool to run the tests
against all supported versions of Python and Django. Install tox
globally, and then simply run:

.. code:: bash

    $ tox

Documentation
-------------

To build the documentation, you’ll need to install ``mkdocs``.

.. code:: bash

    $ pip install mkdocs

To preview the documentation:

.. code:: bash

    $ mkdocs serve
    Running at: http://127.0.0.1:8000/

To build the documentation:

.. code:: bash

    $ mkdocs build

.. _tox: http://tox.readthedocs.org/en/latest/

.. |build-status-image| image:: https://secure.travis-ci.org/rojoca/django-rest-inertia.svg?branch=master
   :target: http://travis-ci.org/rojoca/django-rest-inertia?branch=master
.. |pypi-version| image:: https://img.shields.io/pypi/v/django-rest-inertia.svg
   :target: https://pypi.python.org/pypi/django-rest-inertia
