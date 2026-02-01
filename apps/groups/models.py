import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_groups",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "groups"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_active_members(self):
        User = get_user_model()
        return User.objects.filter(
            memberships__group=self,
            memberships__is_active=True
        )

    def get_member_count(self) -> int:
        return self.memberships.filter(is_active=True).count()

    def is_member(self, user) -> bool:
        return self.memberships.filter(user=user, is_active=True).exists()


class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "memberships"
        constraints = [
            models.UniqueConstraint(fields=["user", "group"], name="unique_user_group"),
        ]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["group", "is_active"]),
        ]

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.user} in {self.group} ({status})"

