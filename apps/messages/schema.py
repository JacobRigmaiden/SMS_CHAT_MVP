from graphene_django import DjangoObjectType

from .models import Message


class MessageType(DjangoObjectType):
    class Meta:
        model = Message
        fields = ["id", "group", "sender", "content", "created_at"]
