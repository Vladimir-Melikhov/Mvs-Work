import uuid
from django.db import models
import os


def service_image_upload_path(instance, filename):
    """Генерирует путь для загрузки изображений сервиса"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('service_images', str(instance.service_id), filename)


class Service(models.Model):
    """Услуга на маркетплейсе"""

    CATEGORY_CHOICES = [
        ('development', 'Разработка'),
        ('design', 'Дизайн'),
        ('marketing', 'Маркетинг'),
        ('writing', 'Копирайтинг'),
        ('video', 'Видео и анимация'),
        ('audio', 'Аудио'),
        ('business', 'Бизнес'),
        ('other', 'Другое'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    owner_id = models.UUIDField(db_index=True)
    owner_name = models.CharField(max_length=255, blank=True)
    owner_avatar = models.TextField(blank=True, null=True)

    ai_template = models.TextField(
        blank=True, 
        null=True,
        help_text="Требования к клиенту (бриф)"
    )
    
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        default='other',
        db_index=True
    )
    tags = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['owner_id']),
        ]

    def __str__(self) -> str:
        return self.title


class ServiceImage(models.Model):
    """Изображения для услуги (до 5 шт)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to=service_image_upload_path,
        max_length=500,
        help_text="Изображение услуги (JPG, PNG, GIF, WEBP до 5MB)"
    )
    order = models.IntegerField(default=0, help_text="Порядок отображения")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'service_images'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['service', 'order']),
        ]
    
    def __str__(self) -> str:
        return f"Image {self.order} for {self.service.title}"


class Deal(models.Model):
    """
    МОДЕЛЬ ЗАКАЗА С ПОДДЕРЖКОЙ АРБИТРАЖА
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен, в работе'),
        ('delivered', 'Сдан на проверку'),
        ('dispute', 'В споре'),
        ('completed', 'Завершён'),
        ('cancelled', 'Отменён'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_room_id = models.UUIDField(db_index=True)
    client_id = models.UUIDField(db_index=True)
    worker_id = models.UUIDField(db_index=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Техническое задание")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    
    revision_count = models.IntegerField(default=0)
    max_revisions = models.IntegerField(default=2)
    
    delivery_message = models.TextField(blank=True)
    completion_message = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    dispute_client_reason = models.TextField(blank=True, help_text="Претензия клиента")
    dispute_worker_defense = models.TextField(blank=True, help_text="Защита исполнителя")
    dispute_created_at = models.DateTimeField(null=True, blank=True, help_text="Когда открыт спор")
    dispute_resolved_at = models.DateTimeField(null=True, blank=True, help_text="Когда разрешен спор")
    dispute_winner = models.CharField(
        max_length=10, 
        blank=True, 
        choices=[('client', 'Клиент'), ('worker', 'Исполнитель')],
        help_text="Кто выиграл спор"
    )
    
    last_message_id = models.UUIDField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'deals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat_room_id', 'status']),
            models.Index(fields=['client_id', 'status']),
            models.Index(fields=['worker_id', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['client_id', 'worker_id'],
                condition=models.Q(status__in=['pending', 'paid', 'delivered', 'dispute']),
                name='unique_active_deal_per_pair'
            )
        ]

    def __str__(self) -> str:
        return f"Deal {self.id} - {self.title} ({self.status})"

    @property
    def is_active(self) -> bool:
        return self.status in ['pending', 'paid', 'delivered', 'dispute']

    @property
    def can_pay(self) -> bool:
        return self.status == 'pending'

    @property
    def can_deliver(self) -> bool:
        return self.status == 'paid'

    @property
    def can_request_revision(self) -> bool:
        return self.status == 'delivered' and self.revision_count < self.max_revisions

    @property
    def can_complete(self) -> bool:
        return self.status == 'delivered'

    @property
    def can_cancel(self) -> bool:
        return self.status in ['pending', 'paid']

    @property
    def can_update_price(self) -> bool:
        return self.status == 'pending'

    @property
    def can_open_dispute(self) -> bool:
        return self.status == 'delivered'

    @property
    def can_worker_refund(self) -> bool:
        return self.status == 'dispute' and not self.dispute_worker_defense

    @property
    def can_worker_defend(self) -> bool:
        return self.status == 'dispute' and not self.dispute_worker_defense

    @property
    def is_dispute_pending_admin(self) -> bool:
        return self.status == 'dispute' and bool(self.dispute_worker_defense) and not self.dispute_winner


class Transaction(models.Model):
    """Финансовая транзакция"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('held', 'Захолдировано'),
        ('captured', 'Списано'),
        ('refunded', 'Возвращено'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    payment_provider = models.CharField(max_length=50, default='stub')
    external_payment_id = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']


class Review(models.Model):
    """Отзывы о заказе"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.OneToOneField(Deal, on_delete=models.CASCADE, related_name='review')
    
    rating = models.IntegerField(help_text="Оценка от 1 до 5")
    comment = models.TextField(blank=True)
    
    reviewer_id = models.UUIDField(help_text="Кто оставил отзыв (обычно клиент)")
    reviewee_id = models.UUIDField(help_text="О ком отзыв (обычно исполнитель)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
