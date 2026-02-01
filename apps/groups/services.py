from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.exceptions import AuthError, ConflictError, NotFound, ValidationError

from .models import Group, Membership

User = get_user_model()

__all__ = ["GroupService", "MembershipService"]


class GroupService:
    @staticmethod
    def create_group(name: str, creator: User) -> Group:
        name = name.strip()
        if not name:
            raise ValidationError("Group name is required")

        try:
            group = Group.objects.create(name=name, created_by=creator)
            MembershipService.join_group(creator, group)
            return group
        except IntegrityError:
            raise ConflictError(f"Group name '{name}' already exists")

    @staticmethod
    def get_group_by_id(group_id: str) -> Group:
        try:
            return Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            raise NotFound("Group not found")

    @staticmethod
    def search_groups(query: str, limit: int = 20):
        if not query or not query.strip():
            return Group.objects.none()
        return Group.objects.filter(name__icontains=query.strip())[:limit]

    @staticmethod
    def list_groups(limit: int = 20, offset: int = 0):
        return Group.objects.all()[offset:offset + limit]


class MembershipService:
    @staticmethod
    def join_group(user: User, group: Group) -> Membership:
        with transaction.atomic():
            existing = Membership.objects.select_for_update().filter(user=user, group=group).first()

            if existing:
                if existing.is_active:
                    raise ConflictError("Already a member of this group")
                existing.is_active = True
                existing.left_at = None
                existing.save(update_fields=["is_active", "left_at"])
                return existing

            max_groups = getattr(settings, "MAX_GROUPS_PER_USER", 10)
            current_count = Membership.objects.filter(user=user, is_active=True).count()
            if current_count >= max_groups:
                raise ValidationError(f"You can only join {max_groups} groups")

            return Membership.objects.create(user=user, group=group)

    @staticmethod
    def leave_group(user: User, group: Group) -> None:
        membership = Membership.objects.filter(user=user, group=group, is_active=True).first()
        if not membership:
            raise NotFound("Not a member of this group")

        if group.created_by == user:
            next_owner = (
                Membership.objects.filter(group=group, is_active=True)
                .exclude(user=user)
                .order_by("joined_at")
                .first()
            )
            group.created_by = next_owner.user if next_owner else None
            group.save(update_fields=["created_by", "updated_at"])

        membership.is_active = False
        membership.left_at = timezone.now()
        membership.save(update_fields=["is_active", "left_at"])

    @staticmethod
    def transfer_ownership(owner: User, group: Group, new_owner: User) -> Group:
        if group.created_by != owner:
            raise AuthError("Only the owner can transfer ownership")
        if not group.is_member(new_owner):
            raise NotFound("Target user is not a member")

        group.created_by = new_owner
        group.save(update_fields=["created_by", "updated_at"])
        return group
