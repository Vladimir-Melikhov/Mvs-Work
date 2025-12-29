import uuid
from django.db import models


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    members = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    deal_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'rooms'

    def __str__(self):
        return f"Room {self.id}"


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Текст'),
        ('system', 'Системное'),
        ('deal_proposal', 'Предложение сделки'),
        ('deal_activated', 'Сделка активирована'),
        ('deal_completion_request', 'Запрос завершения'),
        ('deal_completed', 'Сделка завершена'),
        ('deal_cancelled', 'Сделка отменена'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender_id = models.UUIDField(db_index=True)
    text = models.TextField()

    # Тип сообщения
    message_type = models.CharField(max_length=30, choices=MESSAGE_TYPES, default='text')

    # Для интерактивных карточек сделки
    deal_data = models.JSONField(null=True, blank=True, help_text="Данные сделки для интерактивной карточки")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message {self.id} in Room {self.room_id}"
