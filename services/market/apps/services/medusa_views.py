# services/market/apps/services/medusa_views.py
"""
API-эндпоинты для интеграции с Безопасными сделками Точка Банка (Medusa).

Эндпоинты для воркера (исполнителя):
  POST /api/market/medusa/register-recipient/    — зарегистрироваться как получатель
  POST /api/market/medusa/add-card/              — привязать карту для выплат
  GET  /api/market/medusa/recipient-info/        — информация о получателе и картах
  POST /api/market/medusa/delete-card/           — удалить карту

Эндпоинты для клиента (заказчика):
  POST /api/market/medusa/create-payment/        — создать заказ и получить ссылку на оплату
  GET  /api/market/medusa/payment-status/<deal_id>/  — проверить статус оплаты
  POST /api/market/medusa/confirm-deal/<deal_id>/    — подтвердить выполнение (выплата)
  POST /api/market/medusa/reject-deal/<deal_id>/     — отказаться (возврат)

Утилиты:
  GET  /api/market/medusa/calculate-commission/  — рассчитать комиссии для цены
"""

import os
import uuid
import logging
import requests as http_requests
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from .models import Deal
from .medusa_service import MedusaService, MedusaAPIError

logger = logging.getLogger(__name__)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8001")


def _get_auth_token(request) -> str:
    """Извлечь Bearer token из запроса."""
    auth_header = request.headers.get("Authorization", "")
    return auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else ""


def _get_worker_profile(request) -> dict:
    """Получить профиль воркера через auth service."""
    token = _get_auth_token(request)
    try:
        resp = http_requests.get(
            f"{AUTH_SERVICE_URL}/api/auth/profile/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("data", {})
    except Exception as e:
        logger.error("[Medusa] Ошибка получения профиля: %s", e)
    return {}


def _update_worker_profile(request, fields: dict) -> bool:
    """Обновить поля профиля воркера через auth service."""
    token = _get_auth_token(request)
    try:
        resp = http_requests.patch(
            f"{AUTH_SERVICE_URL}/api/auth/profile/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=fields,
            timeout=5,
        )
        return resp.status_code == 200
    except Exception as e:
        logger.error("[Medusa] Ошибка обновления профиля: %s", e)
        return False


# ──────────────────────────────────────────────────────────────────────────────
# ВОРКЕР: Регистрация получателя
# ──────────────────────────────────────────────────────────────────────────────


class MedusaRegisterRecipientView(APIView):
    """
    POST /api/market/medusa/register-recipient/
    
    Регистрирует воркера как получателя в системе Medusa.
    Вызывается один раз. После этого воркер может привязывать карты.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response(
                {"status": "error", "error": "Только для исполнителей"},
                status=403,
            )

        # Проверяем, не зарегистрирован ли уже
        profile = _get_worker_profile(request)
        if not profile:
            return Response(
                {"status": "error", "error": "Не удалось получить профиль"},
                status=400,
            )

        existing_recipient = profile.get("profile", {}).get("medusa_recipient_ext_id")
        if existing_recipient:
            return Response({
                "status": "success",
                "data": {
                    "recipient_ext_id": existing_recipient,
                    "message": "Вы уже зарегистрированы как получатель",
                },
            })

        # Генерируем UUID получателя = user.id воркера
        recipient_ext_id = str(request.user.id)
        worker_name = (
            profile.get("profile", {}).get("full_name")
            or profile.get("profile", {}).get("company_name")
            or profile.get("email", "Worker")
        )

        try:
            medusa = MedusaService()
            result = medusa.create_recipient(recipient_ext_id, worker_name)

            # Сохраняем в профиле через auth service
            _update_worker_profile(request, {
                "medusa_recipient_ext_id": recipient_ext_id,
                "medusa_recipient_registered": True,
            })

            return Response({
                "status": "success",
                "data": {
                    "recipient_ext_id": recipient_ext_id,
                    "name": worker_name,
                    "message": "Вы зарегистрированы как получатель. Теперь привяжите карту.",
                },
            })

        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка регистрации получателя: %s", e)
            return Response(
                {"status": "error", "error": f"Ошибка банка: {str(e)}"},
                status=502,
            )


# ──────────────────────────────────────────────────────────────────────────────
# ВОРКЕР: Привязка карты
# ──────────────────────────────────────────────────────────────────────────────


class MedusaAddCardView(APIView):
    """
    POST /api/market/medusa/add-card/
    
    Создаёт форму токенизации карты. Воркер переходит по ссылке formUrl
    и вводит данные карты. После этого карта сохраняется в Точке.
    
    Body (опционально):
        {"redirect_url": "https://..."}  — URL после заполнения формы
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response(
                {"status": "error", "error": "Только для исполнителей"},
                status=403,
            )

        recipient_ext_id = str(request.user.id)
        frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")
        redirect_url = request.data.get(
            "redirect_url",
            f"{frontend_url}/profile?card=linked",
        )

        try:
            medusa = MedusaService()
            result = medusa.add_card_payout_method(
                recipient_ext_id=recipient_ext_id,
                redirect_url=redirect_url,
            )

            return Response({
                "status": "success",
                "data": {
                    "form_url": result["formUrl"],
                    "payout_method_ext_id": result["payoutMethodExtId"],
                    "message": "Перейдите по ссылке для ввода данных карты",
                },
            })

        except MedusaAPIError as e:
            # Если получатель не найден — нужно сначала зарегистрироваться
            if e.status_code == 404:
                return Response({
                    "status": "error",
                    "error": "Сначала зарегистрируйтесь как получатель",
                    "action_required": "register_recipient",
                }, status=400)

            logger.error("[Medusa] Ошибка добавления карты: %s", e)
            return Response(
                {"status": "error", "error": f"Ошибка банка: {str(e)}"},
                status=502,
            )


# ──────────────────────────────────────────────────────────────────────────────
# ВОРКЕР: Информация о получателе и картах
# ──────────────────────────────────────────────────────────────────────────────


class MedusaRecipientInfoView(APIView):
    """
    GET /api/market/medusa/recipient-info/
    
    Возвращает информацию о получателе и привязанных картах.
    Если карта привязана — обновляет данные в профиле.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "worker":
            return Response(
                {"status": "error", "error": "Только для исполнителей"},
                status=403,
            )

        recipient_ext_id = str(request.user.id)

        try:
            medusa = MedusaService()
            data = medusa.get_recipient(recipient_ext_id)

            payout_methods = data.get("PayoutMethods", [])
            cards = []
            for pm in payout_methods:
                cards.append({
                    "ext_id": pm.get("extId"),
                    "masked_pan": pm.get("maskedPan", ""),
                    "type": pm.get("type", "CARD"),
                })

            # Обновляем данные о карте в профиле если есть хотя бы одна
            if cards:
                primary_card = cards[0]
                _update_worker_profile(request, {
                    "medusa_card_ext_id": primary_card["ext_id"],
                    "medusa_card_masked_pan": primary_card["masked_pan"],
                    "medusa_card_linked": True,
                })

            return Response({
                "status": "success",
                "data": {
                    "recipient_ext_id": data.get("extId"),
                    "name": data.get("name"),
                    "cards": cards,
                    "has_card": len(cards) > 0,
                },
            })

        except MedusaAPIError as e:
            if e.status_code == 404:
                return Response({
                    "status": "success",
                    "data": {
                        "recipient_ext_id": None,
                        "cards": [],
                        "has_card": False,
                        "registered": False,
                    },
                })

            logger.error("[Medusa] Ошибка получения данных: %s", e)
            return Response(
                {"status": "error", "error": f"Ошибка банка: {str(e)}"},
                status=502,
            )


class MedusaDeleteCardView(APIView):
    """
    POST /api/market/medusa/delete-card/
    
    Body: {"payout_method_ext_id": "uuid-карты"}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response(
                {"status": "error", "error": "Только для исполнителей"},
                status=403,
            )

        payout_method_ext_id = request.data.get("payout_method_ext_id")
        if not payout_method_ext_id:
            return Response(
                {"status": "error", "error": "payout_method_ext_id обязателен"},
                status=400,
            )

        recipient_ext_id = str(request.user.id)

        try:
            medusa = MedusaService()
            success = medusa.delete_card_payout_method(
                recipient_ext_id, payout_method_ext_id
            )

            if success:
                # Обновляем профиль — убираем данные карты
                _update_worker_profile(request, {
                    "medusa_card_ext_id": None,
                    "medusa_card_masked_pan": None,
                    "medusa_card_linked": False,
                })

            return Response({
                "status": "success" if success else "error",
                "message": "Карта удалена" if success else "Не удалось удалить карту",
            })

        except MedusaAPIError as e:
            return Response(
                {"status": "error", "error": f"Ошибка банка: {str(e)}"},
                status=502,
            )


# ──────────────────────────────────────────────────────────────────────────────
# КЛИЕНТ: Создание заказа в Medusa (оплата)
# ──────────────────────────────────────────────────────────────────────────────


class MedusaCreatePaymentView(APIView):
    """
    POST /api/market/medusa/create-payment/
    
    Создаёт заказ в Medusa и возвращает ссылку на оплату.
    Вызывается когда клиент нажимает «Оплатить заказ» в безопасной сделке.
    
    Body: {"deal_id": "uuid-сделки"}
    
    Предусловия:
      - Сделка в статусе pending
      - is_escrow = True
      - У воркера зарегистрирован получатель + привязана карта
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        deal_id = request.data.get("deal_id")
        if not deal_id:
            return Response(
                {"status": "error", "error": "deal_id обязателен"},
                status=400,
            )

        try:
            deal = Deal.objects.select_for_update().get(id=deal_id)
        except Deal.DoesNotExist:
            return Response(
                {"status": "error", "error": "Сделка не найдена"},
                status=404,
            )

        # Проверки
        if str(request.user.id) != str(deal.client_id):
            return Response(
                {"status": "error", "error": "Оплатить может только заказчик"},
                status=403,
            )

        if deal.status != "pending":
            return Response(
                {"status": "error", "error": f"Нельзя оплатить в статусе '{deal.status}'"},
                status=400,
            )

        if not deal.is_escrow:
            return Response(
                {"status": "error", "error": "Это не безопасная сделка"},
                status=400,
            )

        # Если уже есть ссылка на оплату — возвращаем её
        if deal.medusa_payment_url:
            return Response({
                "status": "success",
                "data": {
                    "payment_url": deal.medusa_payment_url,
                    "total_amount": str(deal.medusa_total_amount),
                    "commission_details": {
                        "platform": str(deal.medusa_platform_commission),
                        "tochka": str(deal.medusa_tochka_commission),
                        "acquiring": str(deal.medusa_acquiring_commission),
                        "total": str(deal.medusa_total_commission),
                    },
                    "message": "Используйте ссылку для оплаты",
                },
            })

        # Получаем данные воркера (recipient + card)
        worker_profile = self._get_worker_medusa_data(deal.worker_id)
        if not worker_profile:
            return Response({
                "status": "error",
                "error": "Исполнитель ещё не привязал карту для выплат. "
                         "Попросите исполнителя привязать карту в профиле.",
                "action_required": "worker_card_required",
            }, status=400)

        recipient_ext_id = worker_profile["recipient_ext_id"]
        card_ext_id = worker_profile["card_ext_id"]

        # Получаем email заказчика
        client_email = request.user.email or "customer@mvs-work.ru"

        frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")

        try:
            medusa = MedusaService()
            result = medusa.create_order(
                order_ext_id=str(deal.id),
                service_price=Decimal(str(deal.price)),
                recipient_ext_id=recipient_ext_id,
                card_ext_id=card_ext_id,
                customer_email=client_email,
                redirect_url=f"{frontend_url}/chats/{deal.chat_room_id}?payment=success",
                redirect_fail_url=f"{frontend_url}/chats/{deal.chat_room_id}?payment=failed",
                purpose=f"Оплата заказа: {deal.title[:200]}",
                consumer_id=str(request.user.id),
            )

            commission = result["commission_details"]

            # Сохраняем данные Medusa в сделке
            deal.medusa_order_ext_id = uuid.UUID(result["orderExtId"])
            deal.medusa_service_ext_id = uuid.UUID(result["serviceExtId"])
            deal.medusa_payment_url = result["paymentUrl"]
            deal.medusa_order_status = "created"
            deal.medusa_platform_commission = commission["platform_commission"]
            deal.medusa_tochka_commission = commission["medusa_commission"]
            deal.medusa_acquiring_commission = commission["acquiring_commission"]
            deal.medusa_total_commission = commission["total_commission"]
            deal.medusa_total_amount = commission["total_amount"]
            deal.medusa_recipient_ext_id = uuid.UUID(recipient_ext_id)
            deal.medusa_card_ext_id = uuid.UUID(card_ext_id)
            deal.save()

            return Response({
                "status": "success",
                "data": {
                    "payment_url": result["paymentUrl"],
                    "total_amount": str(commission["total_amount"]),
                    "service_price": str(deal.price),
                    "commission_details": {
                        "platform": str(commission["platform_commission"]),
                        "tochka": str(commission["medusa_commission"]),
                        "acquiring": str(commission["acquiring_commission"]),
                        "total": str(commission["total_commission"]),
                    },
                    "message": "Перейдите по ссылке для оплаты",
                },
            })

        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка создания заказа: %s", e)
            return Response(
                {"status": "error", "error": f"Ошибка платёжного сервиса: {str(e)}"},
                status=502,
            )

    def _get_worker_medusa_data(self, worker_id: str) -> Optional[dict]:
        """Получить данные Medusa воркера через internal API."""
        from .jwt_service import ServiceJWT

        try:
            token = ServiceJWT.generate_service_token("market-medusa", expires_minutes=5)
            resp = http_requests.get(
                f"{AUTH_SERVICE_URL}/api/auth/internal/users/{worker_id}/profile/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )

            if resp.status_code != 200:
                return None

            data = resp.json().get("data", {})
            profile = data.get("profile", {})

            recipient_ext_id = profile.get("medusa_recipient_ext_id")
            card_ext_id = profile.get("medusa_card_ext_id")

            if not recipient_ext_id or not card_ext_id:
                return None

            return {
                "recipient_ext_id": str(recipient_ext_id),
                "card_ext_id": str(card_ext_id),
            }

        except Exception as e:
            logger.error("[Medusa] Ошибка получения данных воркера: %s", e)
            return None


# ──────────────────────────────────────────────────────────────────────────────
# КЛИЕНТ: Проверка статуса оплаты
# ──────────────────────────────────────────────────────────────────────────────


class MedusaPaymentStatusView(APIView):
    """
    GET /api/market/medusa/payment-status/<deal_id>/
    
    Проверяет статус оплаты заказа в Medusa и обновляет сделку.
    Вызывается после редиректа с оплаты или по кнопке «Проверить оплату».
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, deal_id):
        try:
            deal = Deal.objects.get(id=deal_id)
        except Deal.DoesNotExist:
            return Response(
                {"status": "error", "error": "Сделка не найдена"},
                status=404,
            )

        # Проверка участника
        user_id = str(request.user.id)
        if user_id not in [str(deal.client_id), str(deal.worker_id)]:
            return Response(
                {"status": "error", "error": "Нет доступа"},
                status=403,
            )

        if not deal.medusa_order_ext_id:
            return Response({
                "status": "success",
                "data": {
                    "medusa_status": None,
                    "deal_status": deal.status,
                    "message": "Заказ ещё не создан в платёжной системе",
                },
            })

        try:
            medusa = MedusaService()
            order_data = medusa.get_order(str(deal.medusa_order_ext_id))

            medusa_status = order_data.get("status", "unknown")
            deal.medusa_order_status = medusa_status

            # Если оплачен — переводим сделку в статус paid
            if medusa_status == "paid" and deal.status == "pending":
                from .services import DealService
                token = _get_auth_token(request)

                # Используем существующий DealService.pay_deal
                # но с реальной оплатой через Medusa
                deal.status = "paid"
                deal.paid_at = __import__("django.utils.timezone", fromlist=["now"]).now()
                deal.save()

                # Отправляем уведомление в чат
                DealService._send_text_message(
                    chat_room_id=str(deal.chat_room_id),
                    sender_id=str(deal.client_id),
                    text=f"💳 ЗАКАЗ ОПЛАЧЕН (Безопасная сделка)\n\n"
                         f"Сумма: {int(deal.price)}₽\n"
                         f"Комиссия: {deal.medusa_total_commission}₽\n"
                         f"Итого оплачено: {deal.medusa_total_amount}₽\n\n"
                         f"Деньги заморожены до завершения работы.",
                    auth_token=token,
                )

                DealService._send_deal_card(deal, str(deal.client_id), "paid", token)

            deal.save(update_fields=["medusa_order_status"])

            return Response({
                "status": "success",
                "data": {
                    "medusa_status": medusa_status,
                    "deal_status": deal.status,
                    "total_amount": str(deal.medusa_total_amount) if deal.medusa_total_amount else None,
                    "message": self._get_status_message(medusa_status),
                },
            })

        except MedusaAPIError as e:
            return Response(
                {"status": "error", "error": f"Ошибка проверки статуса: {str(e)}"},
                status=502,
            )

    @staticmethod
    def _get_status_message(status: str) -> str:
        messages = {
            "created": "Ожидает оплаты",
            "paid": "Оплачено! Деньги заморожены.",
            "completed": "Деньги выплачены исполнителю",
            "cancelled": "Заказ отменён, деньги возвращены",
        }
        return messages.get(status, f"Статус: {status}")


# ──────────────────────────────────────────────────────────────────────────────
# КЛИЕНТ: Подтверждение / Отказ (Make Decision)
# ──────────────────────────────────────────────────────────────────────────────


class MedusaConfirmDealView(APIView):
    """
    POST /api/market/medusa/confirm-deal/<deal_id>/
    
    Подтвердить выполнение работы — деньги выплачиваются исполнителю.
    Вызывается вместо обычного complete_deal для эскроу-сделок.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, deal_id):
        try:
            deal = Deal.objects.select_for_update().get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Сделка не найдена"}, status=404)

        if str(request.user.id) != str(deal.client_id):
            return Response({"status": "error", "error": "Только заказчик"}, status=403)

        if deal.status != "delivered":
            return Response(
                {"status": "error", "error": "Подтвердить можно только сданную работу"},
                status=400,
            )

        if not deal.medusa_order_ext_id or not deal.medusa_service_ext_id:
            return Response(
                {"status": "error", "error": "Нет данных платёжной системы"},
                status=400,
            )

        try:
            medusa = MedusaService()

            # Подтверждаем в Medusa — деньги пойдут исполнителю
            medusa.make_decision(
                order_ext_id=str(deal.medusa_order_ext_id),
                service_ext_id=str(deal.medusa_service_ext_id),
                decision="confirmed",
            )

            # На STAGE: выполняем sandbox-шаги
            medusa.sandbox_full_cycle_after_decision(
                order_ext_id=str(deal.medusa_order_ext_id),
                service_ext_id=str(deal.medusa_service_ext_id),
                decision="confirmed",
            )

            deal.medusa_order_status = "completed"
            deal.save(update_fields=["medusa_order_status"])

            return Response({
                "status": "success",
                "message": "Работа подтверждена, деньги выплачиваются исполнителю",
            })

        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка подтверждения: %s", e)
            return Response(
                {"status": "error", "error": f"Ошибка платёжного сервиса: {str(e)}"},
                status=502,
            )


class MedusaRejectDealView(APIView):
    """
    POST /api/market/medusa/reject-deal/<deal_id>/
    
    Отказаться от работы — деньги возвращаются заказчику.
    
    ВАЖНО: комиссия за эквайринг (2.2%) удерживается с внутреннего счёта
    платформы даже при отказе.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, deal_id):
        try:
            deal = Deal.objects.select_for_update().get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Сделка не найдена"}, status=404)

        if str(request.user.id) != str(deal.client_id):
            return Response({"status": "error", "error": "Только заказчик"}, status=403)

        if not deal.medusa_order_ext_id or not deal.medusa_service_ext_id:
            return Response(
                {"status": "error", "error": "Нет данных платёжной системы"},
                status=400,
            )

        try:
            medusa = MedusaService()

            # Отказ в Medusa — деньги вернутся заказчику
            medusa.make_decision(
                order_ext_id=str(deal.medusa_order_ext_id),
                service_ext_id=str(deal.medusa_service_ext_id),
                decision="rejected",
            )

            # На STAGE: sandbox-шаги для возврата
            medusa.sandbox_full_cycle_after_decision(
                order_ext_id=str(deal.medusa_order_ext_id),
                service_ext_id=str(deal.medusa_service_ext_id),
                decision="rejected",
            )

            deal.medusa_order_status = "cancelled"
            deal.save(update_fields=["medusa_order_status"])

            return Response({
                "status": "success",
                "message": "Отказ подтверждён, деньги возвращаются на карту",
            })

        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка отказа: %s", e)
            return Response(
                {"status": "error", "error": f"Ошибка платёжного сервиса: {str(e)}"},
                status=502,
            )


# ──────────────────────────────────────────────────────────────────────────────
# УТИЛИТЫ
# ──────────────────────────────────────────────────────────────────────────────


class MedusaCalculateCommissionView(APIView):
    """
    GET /api/market/medusa/calculate-commission/?price=10000
    
    Рассчитать комиссии для заданной цены.
    Полезно для отображения на фронте перед оплатой.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        price = request.query_params.get("price")
        if not price:
            return Response(
                {"status": "error", "error": "Параметр price обязателен"},
                status=400,
            )

        try:
            price_decimal = Decimal(str(price))
            if price_decimal <= 0:
                raise ValueError("Цена должна быть больше нуля")
        except (ValueError, Exception) as e:
            return Response(
                {"status": "error", "error": f"Некорректная цена: {e}"},
                status=400,
            )

        commission = MedusaService.calculate_commission(price_decimal)

        return Response({
            "status": "success",
            "data": {
                "service_price": str(commission["service_price"]),
                "platform_commission": str(commission["platform_commission"]),
                "medusa_commission": str(commission["medusa_commission"]),
                "acquiring_commission": str(commission["acquiring_commission"]),
                "total_commission": str(commission["total_commission"]),
                "total_amount": str(commission["total_amount"]),
                "commission_rate_total": "3.50",  # 0.5 + 0.8 + 2.2
            },
        })
