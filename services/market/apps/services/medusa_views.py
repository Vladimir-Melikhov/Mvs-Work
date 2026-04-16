# services/market/apps/services/medusa_views.py
import os
import uuid
import logging
import requests as http_requests
from decimal import Decimal
from typing import Optional, Dict, Any

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone

from .models import Deal
from .medusa_service import MedusaService, MedusaAPIError

logger = logging.getLogger(__name__)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8001")


def _get_auth_token(request) -> str:
    auth_header = request.headers.get("Authorization", "")
    return auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else ""


def _get_worker_profile(request) -> dict:
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


def _get_worker_medusa_data(worker_id: str) -> Optional[Dict[str, Any]]:
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


class MedusaRegisterRecipientView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        profile = _get_worker_profile(request)
        if not profile:
            return Response({"status": "error", "error": "Не удалось получить профиль"}, status=400)

        existing = profile.get("profile", {}).get("medusa_recipient_ext_id")
        if existing:
            return Response({"status": "success", "data": {"recipient_ext_id": existing, "message": "Уже зарегистрированы"}})

        recipient_ext_id = str(request.user.id)
        worker_name = (
            profile.get("profile", {}).get("full_name")
            or profile.get("profile", {}).get("company_name")
            or profile.get("email", "Worker")
        )

        try:
            medusa = MedusaService()
            medusa.create_recipient(recipient_ext_id, worker_name)
            _update_worker_profile(request, {"medusa_recipient_ext_id": recipient_ext_id, "medusa_recipient_registered": True})
            return Response({"status": "success", "data": {"recipient_ext_id": recipient_ext_id, "name": worker_name, "message": "Зарегистрированы. Теперь привяжите карту."}})
        except MedusaAPIError as e:
            return Response({"status": "error", "error": f"Ошибка банка: {e}"}, status=502)


class MedusaAddCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        recipient_ext_id = str(request.user.id)
        frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")
        redirect_url = request.data.get("redirect_url", f"{frontend_url}/profile?card=linked")

        try:
            medusa = MedusaService()
            result = medusa.add_card_payout_method(recipient_ext_id=recipient_ext_id, redirect_url=redirect_url)

            _update_worker_profile(request, {
                "medusa_card_ext_id": result["payoutMethodExtId"],
                "medusa_card_linked": True,
                "medusa_card_masked_pan": "****",
            })

            return Response({
                "status": "success",
                "data": {
                    "form_url": result["formUrl"],
                    "payout_method_ext_id": result["payoutMethodExtId"],
                    "message": "Перейдите по ссылке для ввода данных карты",
                },
            })
        except MedusaAPIError as e:
            if e.status_code == 404:
                return Response({"status": "error", "error": "Сначала зарегистрируйтесь как получатель", "action_required": "register_recipient"}, status=400)
            return Response({"status": "error", "error": f"Ошибка банка: {e}"}, status=502)


class MedusaRecipientInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        profile = _get_worker_profile(request)
        p = profile.get("profile", {})

        card_ext_id = p.get("medusa_card_ext_id")
        cards = []
        if card_ext_id:
            cards.append({"ext_id": str(card_ext_id), "masked_pan": p.get("medusa_card_masked_pan") or "****", "type": "CARD"})

        return Response({
            "status": "success",
            "data": {
                "recipient_ext_id": str(p["medusa_recipient_ext_id"]) if p.get("medusa_recipient_ext_id") else None,
                "name": p.get("full_name") or p.get("company_name") or "",
                "cards": cards,
                "has_card": bool(p.get("medusa_card_linked")),
                "registered": bool(p.get("medusa_recipient_registered")),
            },
        })


class MedusaDeleteCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        payout_method_ext_id = request.data.get("payout_method_ext_id")
        if not payout_method_ext_id:
            return Response({"status": "error", "error": "payout_method_ext_id обязателен"}, status=400)

        success = False
        try:
            medusa = MedusaService()
            success = medusa.delete_card_payout_method(str(request.user.id), payout_method_ext_id)
        except MedusaAPIError:
            pass

        _update_worker_profile(request, {"medusa_card_ext_id": None, "medusa_card_masked_pan": None, "medusa_card_linked": False})
        return Response({"status": "success", "message": "Карта удалена"})


class MedusaCreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        deal_id = request.data.get("deal_id")
        if not deal_id:
            return Response({"status": "error", "error": "deal_id обязателен"}, status=400)

        try:
            deal = Deal.objects.select_for_update().get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Сделка не найдена"}, status=404)

        if str(request.user.id) != str(deal.client_id):
            return Response({"status": "error", "error": "Оплатить может только заказчик"}, status=403)
        if deal.status != "pending":
            return Response({"status": "error", "error": f"Нельзя оплатить в статусе '{deal.status}'"}, status=400)
        if not deal.is_escrow:
            return Response({"status": "error", "error": "Это не безопасная сделка"}, status=400)

        if deal.medusa_payment_url:
            return Response({"status": "success", "data": {
                "payment_url": deal.medusa_payment_url,
                "total_amount": str(deal.medusa_total_amount),
                "commission_details": {"platform": str(deal.medusa_platform_commission), "tochka": str(deal.medusa_tochka_commission), "acquiring": str(deal.medusa_acquiring_commission), "total": str(deal.medusa_total_commission)},
                "message": "Используйте ссылку для оплаты",
            }})

        worker_profile = _get_worker_medusa_data(str(deal.worker_id))
        if not worker_profile:
            return Response({"status": "error", "error": "Исполнитель не привязал карту.", "action_required": "worker_card_required"}, status=400)

        frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")

        try:
            medusa = MedusaService()
            result = medusa.create_order(
                order_ext_id=str(deal.id),
                service_price=Decimal(str(deal.price)),
                recipient_ext_id=worker_profile["recipient_ext_id"],
                card_ext_id=worker_profile["card_ext_id"],
                customer_email=request.user.email or "customer@mvs-work.ru",
                redirect_url=f"{frontend_url}/chats/{deal.chat_room_id}?payment=success",
                redirect_fail_url=f"{frontend_url}/chats/{deal.chat_room_id}?payment=failed",
                purpose=f"Оплата заказа: {deal.title[:200]}",
                consumer_id=str(request.user.id),
            )

            c = result["commission_details"]
            deal.medusa_order_ext_id = uuid.UUID(result["orderExtId"])
            deal.medusa_service_ext_id = uuid.UUID(result["serviceExtId"])
            deal.medusa_payment_url = result["paymentUrl"]
            deal.medusa_order_status = "created"
            deal.medusa_platform_commission = c["platform_commission"]
            deal.medusa_tochka_commission = c["medusa_commission"]
            deal.medusa_acquiring_commission = c["acquiring_commission"]
            deal.medusa_total_commission = c["total_commission"]
            deal.medusa_total_amount = c["total_amount"]
            deal.medusa_recipient_ext_id = uuid.UUID(worker_profile["recipient_ext_id"])
            deal.medusa_card_ext_id = uuid.UUID(worker_profile["card_ext_id"])
            deal.save()

            return Response({"status": "success", "data": {
                "payment_url": result["paymentUrl"],
                "total_amount": str(c["total_amount"]),
                "service_price": str(deal.price),
                "commission_details": {"platform": str(c["platform_commission"]), "tochka": str(c["medusa_commission"]), "acquiring": str(c["acquiring_commission"]), "total": str(c["total_commission"])},
                "message": "Перейдите по ссылке для оплаты",
            }})
        except MedusaAPIError as e:
            return Response({"status": "error", "error": f"Ошибка платёжного сервиса: {e}"}, status=502)


class MedusaPaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, deal_id):
        try:
            deal = Deal.objects.get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Сделка не найдена"}, status=404)

        if str(request.user.id) not in [str(deal.client_id), str(deal.worker_id)]:
            return Response({"status": "error", "error": "Нет доступа"}, status=403)

        if not deal.medusa_order_ext_id:
            return Response({"status": "success", "data": {"medusa_status": None, "deal_status": deal.status, "message": "Заказ не создан в платёжной системе"}})

        try:
            medusa = MedusaService()
            order_data = medusa.get_order(str(deal.medusa_order_ext_id))
            medusa_status = order_data.get("state") or order_data.get("status", "unknown")
            deal.medusa_order_status = medusa_status

            if medusa_status in ("waiting_services", "waiting_enroll", "paid") and deal.status == "pending":
                from .services import DealService
                deal.status = "paid"
                deal.paid_at = timezone.now()
                deal.save()
                token = _get_auth_token(request)
                DealService._send_text_message(chat_room_id=str(deal.chat_room_id), sender_id=str(deal.client_id),
                    text=f"💳 ЗАКАЗ ОПЛАЧЕН\n\nСумма: {int(deal.price)}₽\nКомиссия: {deal.medusa_total_commission}₽\nИтого: {deal.medusa_total_amount}₽\n\nДеньги заморожены.", auth_token=token)
                DealService._send_deal_card(deal, str(deal.client_id), "paid", token)
            else:
                deal.save(update_fields=["medusa_order_status"])

            return Response({"status": "success", "data": {"medusa_status": medusa_status, "deal_status": deal.status, "total_amount": str(deal.medusa_total_amount) if deal.medusa_total_amount else None, "message": self._msg(medusa_status)}})
        except MedusaAPIError:
            return Response({"status": "success", "data": {"medusa_status": deal.medusa_order_status, "deal_status": deal.status, "message": "Статус из локальной БД"}})

    @staticmethod
    def _msg(s):
        return {"waiting_user_payment": "Ожидает оплаты", "waiting_enroll": "Зачисление", "waiting_services": "Оплачено, заморожено", "finished": "Завершено", "canceled": "Отменён"}.get(s, f"Статус: {s}")


class MedusaConfirmDealView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, deal_id):
        try:
            deal = Deal.objects.select_for_update().get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Не найдена"}, status=404)
        if str(request.user.id) != str(deal.client_id):
            return Response({"status": "error", "error": "Только заказчик"}, status=403)
        if deal.status != "delivered":
            return Response({"status": "error", "error": "Подтвердить можно только сданную работу"}, status=400)
        if not deal.medusa_order_ext_id or not deal.medusa_service_ext_id:
            return Response({"status": "error", "error": "Нет данных платёжной системы"}, status=400)

        try:
            medusa = MedusaService()
            medusa.make_decision(str(deal.medusa_order_ext_id), str(deal.medusa_service_ext_id), "confirmed")
            medusa.sandbox_full_cycle_after_decision(str(deal.medusa_order_ext_id), str(deal.medusa_service_ext_id), "confirmed")
            deal.medusa_order_status = "completed"
            deal.save(update_fields=["medusa_order_status"])
            return Response({"status": "success", "message": "Деньги выплачиваются исполнителю"})
        except MedusaAPIError as e:
            return Response({"status": "error", "error": f"Ошибка: {e}"}, status=502)


class MedusaRejectDealView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, deal_id):
        try:
            deal = Deal.objects.select_for_update().get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Не найдена"}, status=404)
        if str(request.user.id) != str(deal.client_id):
            return Response({"status": "error", "error": "Только заказчик"}, status=403)
        if not deal.medusa_order_ext_id or not deal.medusa_service_ext_id:
            return Response({"status": "error", "error": "Нет данных платёжной системы"}, status=400)

        try:
            medusa = MedusaService()
            medusa.make_decision(str(deal.medusa_order_ext_id), str(deal.medusa_service_ext_id), "rejected")
            medusa.sandbox_full_cycle_after_decision(str(deal.medusa_order_ext_id), str(deal.medusa_service_ext_id), "rejected")
            deal.medusa_order_status = "cancelled"
            deal.save(update_fields=["medusa_order_status"])
            return Response({"status": "success", "message": "Деньги возвращаются"})
        except MedusaAPIError as e:
            return Response({"status": "error", "error": f"Ошибка: {e}"}, status=502)


class MedusaCalculateCommissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        price = request.query_params.get("price")
        if not price:
            return Response({"status": "error", "error": "price обязателен"}, status=400)
        try:
            p = Decimal(str(price))
            if p <= 0:
                raise ValueError
        except (ValueError, Exception):
            return Response({"status": "error", "error": "Некорректная цена"}, status=400)

        c = MedusaService.calculate_commission(p)
        return Response({"status": "success", "data": {
            "service_price": str(c["service_price"]), "platform_commission": str(c["platform_commission"]),
            "medusa_commission": str(c["medusa_commission"]), "acquiring_commission": str(c["acquiring_commission"]),
            "total_commission": str(c["total_commission"]), "total_amount": str(c["total_amount"]),
            "commission_rate_total": "3.50",
        }})
