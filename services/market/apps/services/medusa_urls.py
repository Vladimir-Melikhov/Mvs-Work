# services/market/apps/services/medusa_urls.py
"""
URL-маршруты для API Безопасных сделок (Medusa).

Подключаются в основном urls.py:
    path('medusa/', include('apps.services.medusa_urls')),
"""

from django.urls import path
from .medusa_views import (
    MedusaRegisterRecipientView,
    MedusaAddCardView,
    MedusaRecipientInfoView,
    MedusaDeleteCardView,
    MedusaCreatePaymentView,
    MedusaPaymentStatusView,
    MedusaConfirmDealView,
    MedusaRejectDealView,
    MedusaCalculateCommissionView,
)

urlpatterns = [
    # ── Воркер: управление получателем и картами ──────────────────────────────
    path('register-recipient/', MedusaRegisterRecipientView.as_view(), name='medusa-register-recipient'),
    path('add-card/', MedusaAddCardView.as_view(), name='medusa-add-card'),
    path('recipient-info/', MedusaRecipientInfoView.as_view(), name='medusa-recipient-info'),
    path('delete-card/', MedusaDeleteCardView.as_view(), name='medusa-delete-card'),

    # ── Клиент: оплата и решения ──────────────────────────────────────────────
    path('create-payment/', MedusaCreatePaymentView.as_view(), name='medusa-create-payment'),
    path('payment-status/<uuid:deal_id>/', MedusaPaymentStatusView.as_view(), name='medusa-payment-status'),
    path('confirm-deal/<uuid:deal_id>/', MedusaConfirmDealView.as_view(), name='medusa-confirm-deal'),
    path('reject-deal/<uuid:deal_id>/', MedusaRejectDealView.as_view(), name='medusa-reject-deal'),

    # ── Утилиты ───────────────────────────────────────────────────────────────
    path('calculate-commission/', MedusaCalculateCommissionView.as_view(), name='medusa-calculate-commission'),
]
