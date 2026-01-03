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
    
    # Владелец услуги
    owner_id = models.UUIDField(db_index=True)
    owner_name = models.CharField(max_length=255, blank=True)
    owner_avatar = models.TextField(blank=True, null=True)
    
    # AI-шаблон для генерации ТЗ
    ai_template = models.TextField(
        blank=True, 
        null=True,
        help_text="Шаблон для AI при генерации ТЗ. Например: 'Обязательно уточняй количество страниц, дизайн, сроки'"
    )
    
    # Категория и теги
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        default='other',
        db_index=True,
        help_text="Категория услуги для фильтрации"
    )
    tags = models.JSONField(default=list, blank=True, help_text="Теги для поиска")
    
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
    Сделка - привязана к конкретному чату.
    Каждый чат между клиентом и воркером = потенциальная сделка
    """
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('proposed', 'Предложена'),
        ('active', 'Активна'),
        ('completion_requested', 'Запрос завершения'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Связь с чатом (1 чат = 1 потенциальная сделка)
    chat_room_id = models.UUIDField(unique=True, db_index=True)
    
    # Стороны сделки
    client_id = models.UUIDField(db_index=True)
    worker_id = models.UUIDField(db_index=True)
    
    # Ссылка на услугу (опционально)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Условия сделки (редактируемые!)
    title = models.CharField(max_length=255, default="Новая сделка")
    description = models.TextField(help_text="ТЗ сделки")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Статус и подтверждения
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Кто предложил текущую версию сделки
    proposed_by = models.UUIDField(null=True, blank=True)
    proposed_at = models.DateTimeField(null=True, blank=True)
    
    # Подтверждения
    client_confirmed = models.BooleanField(default=False)
    worker_confirmed = models.BooleanField(default=False)
    
    # История изменений (JSON массив с версиями)
    history = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Когда сделка была активирована (обе стороны подтвердили)
    activated_at = models.DateTimeField(null=True, blank=True)
    
    # ✅ НОВЫЕ ПОЛЯ для запроса завершения
    completion_requested_by = models.UUIDField(null=True, blank=True)
    completion_requested_at = models.DateTimeField(null=True, blank=True)
    
    # Когда завершена
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # ✅ НОВЫЕ ПОЛЯ для отмены
    cancelled_by = models.UUIDField(null=True, blank=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    
    # ✅ НОВОЕ ПОЛЕ - ID последнего сообщения с карточкой сделки (для обновления)
    last_deal_message_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'deals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat_room_id']),
            models.Index(fields=['client_id', 'status']),
            models.Index(fields=['worker_id', 'status']),
        ]

    def __str__(self) -> str:
        return f"Deal {self.id} - {self.title} ({self.status})"


class Transaction(models.Model):
    """Финансовая транзакция для сделки"""
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
    
    # Для будущей интеграции с платежной системой
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
