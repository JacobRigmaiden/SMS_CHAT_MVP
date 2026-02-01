import graphene
from graphene_django import DjangoObjectType

from .models import User
from .services import UserService


def get_user_from_context(info) -> User | None:
    request = info.context
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None
    return UserService.verify_jwt_token(auth_header[7:])


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ["id", "phone_number", "name", "is_verified", "created_at"]

    memberships = graphene.List("apps.groups.schema.MembershipType")

    def resolve_memberships(self, info) -> list:
        return list(self.get_active_memberships())


class UserQuery(graphene.ObjectType):
    me = graphene.Field(UserType)

    def resolve_me(self, info) -> User | None:
        return get_user_from_context(info)
