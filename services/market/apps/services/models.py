import uuid
from django.db import models


class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    owner_id = models.UUIDField(db_index=True)
    owner_name = models.CharField(max_length=255, blank=True)
    owner_avatar = models.TextField(blank=True, null=True)
    ai_template = models.TextField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='orders')
    client_id = models.UUIDField(db_index=True)
    worker_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    agreed_tz = models.TextField(help_text="Final agreed technical specification")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Order {self.id} - {self.status}"