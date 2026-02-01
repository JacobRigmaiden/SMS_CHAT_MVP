import uuid

from django.conf import settings
from django.db import models


class Message(models.Model):
    MAX_CONTENT_LENGTH = 1600

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey("groups.Group", on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "messages"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["group", "-created_at"])]

    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.sender.name} in {self.group.name}: {preview}"
