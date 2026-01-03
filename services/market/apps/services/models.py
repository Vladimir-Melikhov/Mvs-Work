import uuid
from django.db import models


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
        help_text="Требования к клиенту (что он должен предоставить)"
    )
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        default='other',
        db_index=True,
        help_text="Категория услуги для фильтрации"
    )
    tags = models.JSONField(default=list,
                            blank=True,
                            help_text="Теги для поиска")
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


class Deal(models.Model):
    """
    УЛУЧШЕННАЯ МОДЕЛЬ ЗАКАЗА
    """
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('pending_payment', 'Ожидает оплаты'),
        ('in_progress', 'В работе'),
        ('revision_requested', 'Нужна доработка'),
        ('delivered', 'Сдан на проверку'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
        ('disputed', 'Спор'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_room_id = models.UUIDField(unique=True, db_index=True)
    client_id = models.UUIDField(db_index=True)
    worker_id = models.UUIDField(db_index=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255, default="Новый заказ")
    description = models.TextField(help_text="Техническое задание")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    client_agreed = models.BooleanField(default=False, help_text="Клиент согласен с условиями")
    worker_agreed = models.BooleanField(default=False, help_text="Воркер согласен с условиями")
    proposed_by = models.UUIDField(null=True, blank=True)
    proposed_at = models.DateTimeField(null=True, blank=True)
    payment_completed = models.BooleanField(default=False, help_text="Оплата прошла")
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_message = models.TextField(blank=True, help_text="Сообщение воркера при сдаче")
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_message = models.TextField(blank=True, help_text="Отзыв клиента")
    cancelled_by = models.UUIDField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    change_request_by = models.UUIDField(null=True, blank=True, help_text="Кто запросил изменение условий")
    change_request_reason = models.TextField(blank=True, help_text="Причина запроса изменений")
    change_request_pending = models.BooleanField(default=False)
    revision_count = models.IntegerField(default=0, help_text="Сколько раз запрашивались правки")
    max_revisions = models.IntegerField(default=3, help_text="Максимум бесплатных доработок")
    history = models.JSONField(default=list, blank=True)
    last_deal_message_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'deals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat_room_id']),
            models.Index(fields=['client_id', 'status']),
            models.Index(fields=['worker_id', 'status']),
            models.Index(fields=['status', 'payment_completed']),
        ]

    def __str__(self) -> str:
        return f"Deal {self.id} - {self.title} ({self.status})"

    def can_edit_terms(self) -> bool:
        """Можно ли редактировать условия (только до оплаты)"""
        return not self.payment_completed and self.status in ['draft', 'pending_payment']

    def can_pay(self) -> bool:
        """Можно ли оплатить"""
        return self.status == 'pending_payment' and self.client_agreed and self.worker_agreed

    def can_deliver(self) -> bool:
        """Может ли воркер сдать работу"""
        return self.status == 'in_progress' and self.payment_completed

    def can_request_revision(self) -> bool:
        """Может ли клиент запросить доработку"""
        return self.status == 'delivered' and self.revision_count < self.max_revisions

    def can_complete(self) -> bool:
        """Может ли клиент завершить и принять работу"""
        return self.status == 'delivered' and self.payment_completed

    def can_cancel(self) -> bool:
        """Можно ли отменить"""
        return self.status not in ['completed', 'disputed']


class Transaction(models.Model):
    """Финансовая транзакция для заказа"""
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
    payment_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Transaction {self.id} - {self.status}"
