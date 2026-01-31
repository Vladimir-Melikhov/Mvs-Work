import uuid
from django.db import models
import os


def message_attachment_upload_path(instance, filename):
    """Генерирует путь для загрузки вложений сообщений"""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    # Используем временную папку для файлов без сообщения
    return os.path.join('message_attachments', 'temp', new_filename)


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    members = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Добавлено для сортировки

    deal_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'rooms'
        indexes = [
            models.Index(fields=['-updated_at']),  # Индекс для быстрой сортировки
        ]

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

    message_type = models.CharField(max_length=30, choices=MESSAGE_TYPES, default='text')
    deal_data = models.JSONField(null=True, blank=True, help_text="Данные сделки для интерактивной карточки")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),  # Индекс для последнего сообщения
        ]

    def __str__(self):
        return f"Message {self.id} in Room {self.room_id}"
    
    def save(self, *args, **kwargs):
        """При сохранении обновляем updated_at комнаты"""
        super().save(*args, **kwargs)
        # Обновляем время последнего обновления комнаты
        Room.objects.filter(id=self.room_id).update(updated_at=self.created_at)


class ReadReceipt(models.Model):
    """Отметки о прочтении сообщений"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='read_receipts')
    user_id = models.UUIDField(db_index=True)
    last_read_message = models.ForeignKey(
        Message, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Последнее прочитанное сообщение"
    )
    last_read_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'read_receipts'
        unique_together = [['room', 'user_id']]
        indexes = [
            models.Index(fields=['room', 'user_id']),
        ]
    
    def __str__(self):
        return f"ReadReceipt for user {self.user_id} in room {self.room_id}"


class MessageAttachment(models.Model):
    """Файловые вложения к сообщениям"""
    
    DISPLAY_MODE_CHOICES = [
        ('inline', 'Показать как изображение'),
        ('attachment', 'Показать как файл для скачивания'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    file = models.FileField(
        upload_to=message_attachment_upload_path,
        max_length=500,
        help_text="Файл-вложение (до 20MB)",
        null=True,
        blank=True
    )
    external_url = models.URLField(
        max_length=1000,
        blank=True,
        help_text="URL файла на внешнем сервисе (например, market service)"
    )
    filename = models.CharField(max_length=255, help_text="Оригинальное имя файла")
    file_size = models.IntegerField(help_text="Размер файла в байтах")
    content_type = models.CharField(max_length=100, blank=True)
    display_mode = models.CharField(
        max_length=20,
        choices=DISPLAY_MODE_CHOICES,
        default='inline',
        help_text="Как отображать файл в чате"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message_attachments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Attachment {self.filename} for Message {self.message_id}"
    
    def get_file_url(self):
        """Возвращает URL файла (либо локальный, либо external)"""
        if self.external_url:
            return self.external_url
        if self.file:
            return self.file.url
        return None
