__version__ = "0.1.0"

from rest_framework.requests import Request


@property
def inertia(self):
    """an InertiaObject for the request"""
    return self._inertia

@inertia.setter
def inertia(self, value):
    self._inertia = value

@inertia.deleter
def inertia(self):
    del self._inertia


"""
Add an inertia property to the rest_framework Request object
"""
Request.inertia = inertia

