from collections import OrderedDict
from django.contrib import messages
from django.utils.module_loading import import_string
from rest_framework import serializers, fields
from rest_framework.relations import PKOnlyObject

from .config import SHARED_DATA_SERIALIZER


class SharedSerializerBase(serializers.Serializer):
    """
    SharedSerializerBase is used to include common data across
    requests in each inertia response.

    You can define your own SharedSerializer by setting the
    INERTIA_SHARED_SERIALIZER_CLASS in your settings.

    Each SharedSerializer receives an Inertia as the
    instance to be "serialized" as well as the render_context
    as its context.

    The SharedSerializer serializes the Request by merging
    its own fields with the data on the Inertia. Data from
    the Inertia is never overwritten by the SharedSerializer.
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

    @property
    def is_conflict(self):
        return self.context["request"].status_code == status.HTTP_409_CONFLICT

    def get_attribute(self, instance):
        return instance


class FlashSerializer(SharedField):
    def to_representation(self, value):
        # no need to iterate (and mark used) messages if 409 response
        flash = {}
        if not self.is_conflict:
            storage = messages.get_messages(self.context["request"])
            for message in storage:
                flash[message.level_tag] = message.message
        return flash


class SessionSerializerField(SharedField):
    def __init__(self, session_field, **kwargs):
        self.session_field = session_field
        super(SessionSerializerField, self).__init__(**kwargs)

    def to_representation(self, value):
        if not self.is_conflict and self.session_field in self.context["request"].session:
            return self.context["request"].session[self.session_field]
        return None


class DefaultSharedSerializer(SharedSerializerBase):
    errors = SessionSerializerField(session_field="errors", default=OrderedDict(), source='*')
    flash = FlashSerializer(default=OrderedDict(), source='*')


class InertiaSerializer(serializers.Serializer):
    component = serializers.CharField()
    props = serializers.SerializerMethodField()
    version = serializers.CharField()
    url = serializers.URLField()

    def get_props(self, obj):
        serializer_class = import_string(SHARED_DATA_SERIALIZER)
        serializer = serializer_class(self.context["request"], context=self.context)
        return serializer.data
