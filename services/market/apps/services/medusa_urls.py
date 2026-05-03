"""
services/market/apps/services/medusa_urls.py

URL-маршруты для Medusa API (безопасные сделки Tochka).
"""
from django.urls import path
from . import medusa_views

urlpatterns = [
    # Получатель (воркер)
    path(
        "register-recipient/",
        medusa_views.MedusaRegisterRecipientView.as_view(),
        name="medusa-register-recipient",
    ),
    path(
        "recipient-info/",
        medusa_views.MedusaRecipientInfoView.as_view(),
        name="medusa-recipient-info",
    ),

    # Карты
    path(
        "add-card/",
        medusa_views.MedusaAddCardView.as_view(),
        name="medusa-add-card",
    ),
    path(
        "delete-card/",
        medusa_views.MedusaDeleteCardView.as_view(),
        name="medusa-delete-card",
    ),

    # Отладочные (только stage)
    path(
        "reset-recipient/",
        medusa_views.MedusaResetRecipientView.as_view(),
        name="medusa-reset-recipient",
    ),
    path(
        "force-link-card/",
        medusa_views.MedusaForceLinkCardView.as_view(),
        name="medusa-force-link-card",
    ),

    # Платежи (сделки)
    path(
        "create-payment/",
        medusa_views.MedusaCreatePaymentView.as_view(),
        name="medusa-create-payment",
    ),
    path(
        "payment-status/<uuid:deal_id>/",
        medusa_views.MedusaPaymentStatusView.as_view(),
        name="medusa-payment-status",
    ),
    path(
        "confirm-deal/<uuid:deal_id>/",
        medusa_views.MedusaConfirmDealView.as_view(),
        name="medusa-confirm-deal",
    ),
    path(
        "reject-deal/<uuid:deal_id>/",
        medusa_views.MedusaRejectDealView.as_view(),
        name="medusa-reject-deal",
    ),

    # Утилита
    path(
        "calculate-commission/",
        medusa_views.MedusaCalculateCommissionView.as_view(),
        name="medusa-calculate-commission",
    ),
]
