from apps.groups.models import Group
from apps.sms.services import SMSService
from core.exceptions import AuthError, ValidationError

from .models import Message

__all__ = ["MessageService"]


class MessageService:
    @staticmethod
    def send_message(sender, group: Group, content: str) -> Message:
        if not group.is_member(sender):
            raise AuthError("You are not a member of this group")

        content = content.strip() if content else ""
        if not content:
            raise ValidationError("Message cannot be empty")
        if len(content) > Message.MAX_CONTENT_LENGTH:
            raise ValidationError(f"Message exceeds {Message.MAX_CONTENT_LENGTH} characters")

        message = Message.objects.create(group=group, sender=sender, content=content)

        recipients = list(
            group.get_active_members()
            .exclude(id=sender.id)
            .values_list("phone_number", flat=True)
        )
        if recipients:
            try:
                SMSService().send_bulk(recipients, f"[{group.name}] {sender.name}: {content}")
            except Exception:
                pass

        return message

    @staticmethod
    def get_group_messages(group: Group, limit: int = 50):
        return (
            Message.objects
            .filter(group=group)
            .select_related("sender")
            .order_by("-created_at")[:limit]
        )
