import logging
from collections import OrderedDict
from django.contrib import messages
from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework import serializers, fields
from rest_framework.relations import PKOnlyObject

logger = logging.getLogger('django')


class SharedSerializerBase(serializers.Serializer):
    """
    SharedSerializerBase is used to include common data across
    requests in each inertia response.

    You can define your own SharedSerializer by setting the
    INERTIA_SHARED_SERIALIZER_CLASS in your settings.

    Each SharedSerializer receives an InertiaObject as the
    instance to be "serialized" as well as the render_context
    as its context.

    The SharedSerializer serializes the Request by merging
    its own fields with the data on the InertiaObject. Data from
    the InertiaObject is never overwritten by the SharedSerializer.
    In this way you can override the default shared data in your
    own views if necessary.

    Since the SharedSerializer is used for every Inertia response
    you should avoid long running operations and always return
    from methods as soon as possible.

    """
    def __init__(self, instance=None, *args, **kwargs):
        # exclude fields already in data or not in instance.partial_data
        exclude = instance.inertia.data.keys()
        for field in self.fields:
            if instance.inertia.partial_data and field not in instance.inertia.partial_data:
                exclude.append(field)

        for field in exclude:
            self.fields.pop(field)

        super(SharedSerializerBase, self).__init__(instance, *args, **kwargs)

    def to_representation(self, instance):
        # merge the shared data with the component data
        # ensuring that component data is always prioritized
        data = super(SharedSerializerBase, self).to_representation(instance)
        data.update(instance.inertia.data)
        return data


class SharedField(fields.Field):
    """
    Shared fields by default are Read-only and require a context
    """
    requires_context = True

    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return instance


class FlashSerializer(SharedField):
    def to_representation(self, value):
        flash = {}
        try:
            storage = messages.get_messages(self.context["request"])
            for message in storage:
                flash[message.level_tag] = message.message
        except:
            pass
        return flash


class SessionErrorsSerializer(SharedField):
    def to_representation(self, value):
        try:
            return self.context["request"].session["errors"] or {}
        except:
            pass
        return {}


class DefaultSharedSerializer(SharedSerializerBase):
    errors = SessionErrorsSerializer(default=OrderedDict(), source='*')
    flash = FlashSerializer(default=OrderedDict(), source='*')


class InertiaSerializer(serializers.Serializer):
    component = serializers.CharField()
    props = serializers.SerializerMethodField()
    version = serializers.CharField()
    url = serializers.URLField()

    def get_props(self, obj):
        if hasattr(settings, 'INERTIA_SHARED_SERIALIZER_CLASS'):
            serializer_class = import_string(settings.INERTIA_SHARED_SERIALIZER_CLASS)

        else:
            serializer_class = DefaultSharedSerializer
        serializer = serializer_class(self.context["request"], context=self.context)
        return serializer.data
