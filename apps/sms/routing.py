import re

from django.contrib.auth import get_user_model
from django.db.models import Max

from apps.groups.models import Group

User = get_user_model()

GROUP_PREFIX_PATTERN = re.compile(r"^#(\S+)\s+(.+)$", re.DOTALL)


class SMSRouter:
    @staticmethod
    def parse_group_prefix(message: str):
        if not message:
            return None, ""

        message = message.strip()
        match = GROUP_PREFIX_PATTERN.match(message)
        if match:
            return match.group(1), match.group(2).strip()
        return None, message

    @staticmethod
    def get_target_group(user, message: str):
        group_name, content = SMSRouter.parse_group_prefix(message)

        user_groups = list(Group.objects.filter(
            memberships__user=user,
            memberships__is_active=True,
        ))

        if not user_groups:
            return None, content

        if group_name:
            for group in user_groups:
                if group.name.lower() == group_name.lower():
                    return group, content
            for group in user_groups:
                if group_name.lower() in group.name.lower():
                    return group, content
            return None, content

        if len(user_groups) == 1:
            return user_groups[0], content

        recent = SMSRouter.get_most_recent_group(user)
        return (recent, content) if recent else (None, content)

    @staticmethod
    def get_most_recent_group(user):
        return (
            Group.objects
            .filter(memberships__user=user, memberships__is_active=True)
            .annotate(latest_message=Max("messages__created_at"))
            .order_by("-latest_message")
            .first()
        )

    @staticmethod
    def get_clarification_message(user) -> str:
        groups = Group.objects.filter(memberships__user=user, memberships__is_active=True)
        if not groups.exists():
            return "You're not in any groups. Join a group at the website to start chatting."

        group_list = ", ".join(g.name for g in groups)
        return f"Which group? Reply with #groupname followed by your message. Your groups: {group_list}"
