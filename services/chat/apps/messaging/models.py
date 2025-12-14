import uuid
from django.db import models


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    members = models.JSONField(default=list, help_text="List of user IDs in room")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return f"Room {self.id}"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender_id = models.UUIDField(db_index=True)
    text = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    is_system = models.BooleanField(default=False, help_text="System notification message")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"Message from {self.sender_id} in {self.room_id}"
