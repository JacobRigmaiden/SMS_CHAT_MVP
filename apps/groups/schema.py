import graphene
from django.db.models import Count, Q
from graphene_django import DjangoObjectType

from .models import Group, Membership


class GroupType(DjangoObjectType):
    class Meta:
        model = Group
        fields = ["id", "name", "created_by", "created_at"]

    member_count = graphene.Int()
    members = graphene.List("apps.users.schema.UserType")
    messages = graphene.List("apps.messages.schema.MessageType", first=graphene.Int(default_value=50))

    def resolve_member_count(self, info) -> int:
        if hasattr(self, "_member_count"):
            return self._member_count
        return self.get_member_count()

    def resolve_members(self, info) -> list:
        return list(self.get_active_members())

    def resolve_messages(self, info, first: int) -> list:
        return list(self.messages.select_related("sender").order_by("-created_at")[:first])


class MembershipType(DjangoObjectType):
    class Meta:
        model = Membership
        fields = ["id", "user", "group", "is_active", "joined_at", "left_at"]


class GroupQuery(graphene.ObjectType):
    group = graphene.Field(GroupType, id=graphene.UUID(required=True))
    groups = graphene.List(GroupType, limit=graphene.Int(default_value=20))
    search_groups = graphene.List(GroupType, query=graphene.String(required=True), limit=graphene.Int(default_value=20))

    def resolve_group(self, info, id):
        try:
            return Group.objects.get(id=id)
        except Group.DoesNotExist:
            return None

    def resolve_groups(self, info, limit: int):
        return (
            Group.objects
            .annotate(_member_count=Count("memberships", filter=Q(memberships__is_active=True)))
            .order_by("-created_at")[:limit]
        )

    def resolve_search_groups(self, info, query: str, limit: int):
        if not query or not query.strip():
            return []
        return (
            Group.objects
            .filter(name__icontains=query.strip())
            .annotate(_member_count=Count("memberships", filter=Q(memberships__is_active=True)))
            [:limit]
        )
