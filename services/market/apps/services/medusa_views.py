"""
services/market/apps/services/medusa_views.py
"""
import os
import json
import uuid
import logging
import requests as http_requests
from decimal import Decimal
from typing import Optional, Dict

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone

from .models import Deal
from .medusa_service import MedusaService, MedusaAPIError

logger = logging.getLogger(__name__)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8001")

# Статусы Get Order V2, означающие что заказ оплачен
PAID_STATES = {
    "waiting_enroll",
    "waiting_services",
    "waiting_compensation",
    "waiting_commissions",
    "finished",
    "paid",
}

CANCELED_STATES = {"canceled", "cancelled", "failed"}


def _auth_token(request) -> str:
    h = request.headers.get("Authorization", "")
    return h.split(" ", 1)[1] if h.startswith("Bearer ") else ""


def _get_my_profile(request) -> dict:
    token = _auth_token(request)
    try:
        r = http_requests.get(
            f"{AUTH_SERVICE_URL}/api/auth/profile/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if r.status_code == 200:
            return r.json().get("data", {})
    except Exception as e:
        logger.error("[Medusa] profile GET: %s", e)
    return {}


def _patch_my_profile(request, fields: dict) -> bool:
    token = _auth_token(request)
    try:
        r = http_requests.patch(
            f"{AUTH_SERVICE_URL}/api/auth/profile/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=fields,
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error("[Medusa] profile PATCH: %s", e)
    return False


def _get_worker_medusa_data(worker_id: str) -> Optional[Dict[str, str]]:
    from .jwt_service import ServiceJWT
    try:
        token = ServiceJWT.generate_service_token("market-medusa", expires_minutes=5)
        r = http_requests.get(
            f"{AUTH_SERVICE_URL}/api/auth/internal/users/{worker_id}/profile/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if r.status_code != 200:
            return None

        p = r.json().get("data", {}).get("profile", {})
        recipient_id = p.get("medusa_recipient_ext_id")
        card_id = p.get("medusa_card_ext_id")
        linked = p.get("medusa_card_linked", False)

        if not recipient_id or not card_id or not linked:
            return None
        return {"recipient_ext_id": str(recipient_id), "card_ext_id": str(card_id)}
    except Exception as e:
        logger.error("[Medusa] worker data %s: %s", worker_id, e)
        return None


# ═══════════════════════════════════════════════════════════════════════════

class MedusaRegisterRecipientView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        profile_data = _get_my_profile(request)
        if not profile_data:
            return Response({"status": "error", "error": "Не удалось получить профиль"}, status=500)
        p = profile_data.get("profile", {})

        if p.get("medusa_recipient_registered") and p.get("medusa_recipient_ext_id"):
            return Response({"status": "success", "data": {
                "recipient_ext_id": str(p["medusa_recipient_ext_id"]),
                "message": "Уже зарегистрированы. Привяжите карту.",
            }})

        recipient_ext_id = str(request.user.id)
        name = p.get("full_name") or p.get("company_name") or profile_data.get("email", "Worker")

        try:
            medusa = MedusaService()
            medusa.create_recipient(recipient_ext_id, name)
            _patch_my_profile(request, {
                "medusa_recipient_ext_id": recipient_ext_id,
                "medusa_recipient_registered": True,
            })
            return Response({"status": "success", "data": {
                "recipient_ext_id": recipient_ext_id,
                "message": "Регистрация успешна! Привяжите карту.",
            }})
        except MedusaAPIError as e:
            logger.error("[Medusa] create_recipient: %s", e)
            try:
                existing = MedusaService().get_recipient(recipient_ext_id)
                if existing and existing.get("extId"):
                    _patch_my_profile(request, {
                        "medusa_recipient_ext_id": recipient_ext_id,
                        "medusa_recipient_registered": True,
                    })
                    return Response({"status": "success", "data": {
                        "recipient_ext_id": recipient_ext_id,
                        "message": "Регистрация восстановлена.",
                    }})
            except Exception:
                pass
            return Response({"status": "error", "error": f"Ошибка банка: {str(e)[:200]}"}, status=502)


class MedusaAddCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        p = _get_my_profile(request).get("profile", {})
        if not p.get("medusa_recipient_registered") or not p.get("medusa_recipient_ext_id"):
            return Response({"status": "error", "error": "Сначала зарегистрируйтесь", "action_required": "register_recipient"}, status=400)

        recipient_ext_id = str(p["medusa_recipient_ext_id"])
        frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")
        redirect_url = request.data.get("redirect_url", f"{frontend_url}/profile?card_added=1")
        payout_method_ext_id = str(uuid.uuid4())

        try:
            medusa = MedusaService()
            result = medusa.add_card_payout_method(recipient_ext_id, redirect_url, payout_method_ext_id)
            _patch_my_profile(request, {
                "medusa_card_ext_id": payout_method_ext_id,
                "medusa_card_linked": False,
                "medusa_card_masked_pan": None,
            })
            return Response({"status": "success", "data": {
                "form_url": result["formUrl"],
                "payout_method_ext_id": payout_method_ext_id,
                "message": "Перейдите по ссылке для ввода данных карты",
            }})
        except MedusaAPIError as e:
            if e.status_code == 404:
                _patch_my_profile(request, {"medusa_recipient_registered": False})
                return Response({"status": "error", "error": "Получатель не найден. Зарегистрируйтесь заново.", "action_required": "register_recipient"}, status=400)
            return Response({"status": "error", "error": f"Ошибка банка: {str(e)[:200]}"}, status=502)


class MedusaRecipientInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        p = _get_my_profile(request).get("profile", {})
        registered = bool(p.get("medusa_recipient_registered"))
        recipient_ext_id = p.get("medusa_recipient_ext_id")

        result = {
            "recipient_ext_id": str(recipient_ext_id) if recipient_ext_id else None,
            "registered": registered,
            "has_card": False,
            "cards": [],
            "card_ext_id": str(p["medusa_card_ext_id"]) if p.get("medusa_card_ext_id") else None,
            "medusa_card_ext_id": str(p["medusa_card_ext_id"]) if p.get("medusa_card_ext_id") else None,
        }

        if not registered or not recipient_ext_id:
            return Response({"status": "success", "data": result})

        try:
            medusa = MedusaService()
            recipient = medusa.get_recipient(str(recipient_ext_id))
            logger.info("[Medusa] get_recipient response: %s", json.dumps(recipient, default=str)[:2000])

            payout_methods = recipient.get("PayoutMethods") or []

            cards = [m for m in payout_methods if m.get("methodType", "").upper() in ("CARD", "CARD_PAYOUT_METHOD")]
            if not cards and payout_methods:
                cards = payout_methods

            if cards:
                main = cards[0]
                card_ext_id = main.get("extId", "")
                masked_pan = main.get("maskedCardNumber", "****")

                if not p.get("medusa_card_linked") or str(p.get("medusa_card_ext_id") or "") != card_ext_id:
                    _patch_my_profile(request, {
                        "medusa_card_ext_id": card_ext_id,
                        "medusa_card_linked": True,
                        "medusa_card_masked_pan": masked_pan,
                    })

                result["has_card"] = True
                result["cards"] = [{"ext_id": c.get("extId", ""), "masked_pan": c.get("maskedCardNumber", "****"), "type": c.get("methodType", "CARD")} for c in cards]
            else:
                if p.get("medusa_card_linked"):
                    _patch_my_profile(request, {"medusa_card_linked": False, "medusa_card_masked_pan": None})

        except MedusaAPIError as e:
            logger.warning("[Medusa] get_recipient: %s", e)
            if p.get("medusa_card_linked") and p.get("medusa_card_ext_id"):
                result["has_card"] = True
                result["cards"] = [{"ext_id": str(p["medusa_card_ext_id"]), "masked_pan": p.get("medusa_card_masked_pan") or "****", "type": "CARD"}]
        except Exception as e:
            logger.error("[Medusa] recipient-info: %s", e)

        return Response({"status": "success", "data": result})


class MedusaDeleteCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        payout_method_ext_id = request.data.get("payout_method_ext_id")
        if not payout_method_ext_id:
            return Response({"status": "error", "error": "payout_method_ext_id обязателен"}, status=400)

        p = _get_my_profile(request).get("profile", {})
        recipient_ext_id = p.get("medusa_recipient_ext_id")

        if not recipient_ext_id:
            _patch_my_profile(request, {"medusa_card_ext_id": None, "medusa_card_masked_pan": None, "medusa_card_linked": False})
            return Response({"status": "success", "message": "Карта удалена (локально)"})

        medusa = MedusaService()
        ok, err_code = medusa.delete_card_payout_method(str(recipient_ext_id), payout_method_ext_id)

        if not ok:
            if err_code == 'has_active_deal':
                return Response({
                    "status": "error",
                    "error": "Нельзя удалить карту, пока есть незавершённые сделки. Дождитесь завершения всех активных сделок."
                }, status=400)
            return Response({
                "status": "error",
                "error": "Не удалось удалить карту в банке"
            }, status=502)

        _patch_my_profile(request, {"medusa_card_ext_id": None, "medusa_card_masked_pan": None, "medusa_card_linked": False})
        return Response({"status": "success", "message": "Карта удалена"})


# ─── Debug (stage) ────────────────────────────────────────────────────────────

class MedusaResetRecipientView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if os.getenv("MEDUSA_ENV", "stage").lower() != "stage":
            return Response({"status": "error", "error": "Только stage"}, status=403)
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)
        _patch_my_profile(request, {
            "medusa_recipient_ext_id": None, "medusa_recipient_registered": False,
            "medusa_card_ext_id": None, "medusa_card_linked": False, "medusa_card_masked_pan": None,
        })
        return Response({"status": "success", "message": "Данные сброшены."})


class MedusaForceLinkCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if os.getenv("MEDUSA_ENV", "stage").lower() != "stage":
            return Response({"status": "error", "error": "Только stage"}, status=403)
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)
        p = _get_my_profile(request).get("profile", {})
        if not p.get("medusa_card_ext_id"):
            return Response({"status": "error", "error": "Сначала нажмите «Привязать карту»"}, status=400)
        _patch_my_profile(request, {
            "medusa_card_linked": True,
            "medusa_card_masked_pan": p.get("medusa_card_masked_pan") or "4111****1111",
        })
        return Response({"status": "success", "message": "Карта помечена как привязанная (stage)"})


# ─── Payments ─────────────────────────────────────────────────────────────────

class MedusaCreatePaymentView(APIView):
    """
    Создаёт ордер в Medusa и возвращает ссылку на оплату.
    После сохранения сделки — обновляет deal_card в чате через WebSocket,
    чтобы фронт сразу увидел кнопки «Перейти к оплате» / «Я оплатил».

    ВАЖНО: order_ext_id в банке генерируется заново при каждом создании,
    а не берётся из id сделки. Иначе после смены цены Точка вернёт старый
    ордер с прежней суммой по тому же orderExtId.
    """
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
            return Response({"status": "error", "error": "Только заказчик"}, status=403)
        if not deal.is_escrow:
            return Response({"status": "error", "error": "Не безопасная сделка"}, status=400)
        if deal.status != "pending":
            return Response({"status": "error", "error": f"Нельзя в статусе '{deal.status}'"}, status=400)

        # Если ссылка уже есть — сразу обновляем карточку в чате (на случай если
        # она там устарела) и отдаём существующую
        if deal.medusa_payment_url and deal.medusa_order_ext_id:
            try:
                from .services import DealService
                DealService._send_deal_card(deal, str(request.user.id), "payment_link_created", _auth_token(request))
            except Exception as e:
                logger.error("[Medusa] resend deal_card error: %s", e)

            return Response({"status": "success", "data": {
                "payment_url": deal.medusa_payment_url,
                "total_amount": str(deal.medusa_total_amount or deal.price),
                "commission_details": {
                    "platform": str(deal.medusa_platform_commission or 0),
                    "tochka": str(deal.medusa_tochka_commission or 0),
                    "acquiring": str(deal.medusa_acquiring_commission or 0),
                    "total": str(deal.medusa_total_commission or 0),
                },
            }})

        worker_data = _get_worker_medusa_data(str(deal.worker_id))
        if not worker_data:
            return Response({"status": "error", "error": "Исполнитель не привязал карту.", "action_required": "worker_card_required"}, status=400)

        frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")

        # Генерируем НОВЫЙ order_ext_id для банка при каждом создании платежа.
        # Точка идемпотентна по orderExtId — если переслать тот же id, вернёт
        # тот же payment_url и старую сумму, даже если в нашей БД уже другая цена.
        new_order_ext_id = str(uuid.uuid4())

        try:
            medusa = MedusaService()
            result = medusa.create_order(
                order_ext_id=new_order_ext_id,
                service_price=Decimal(str(deal.price)),
                recipient_ext_id=worker_data["recipient_ext_id"],
                card_ext_id=worker_data["card_ext_id"],
                customer_email=request.user.email or "customer@mvs-work.ru",
                redirect_url=f"{frontend_url}/chats/{deal.chat_room_id}?payment=success",
                redirect_fail_url=f"{frontend_url}/chats/{deal.chat_room_id}?payment=failed",
                purpose=f"Оплата: {deal.title[:200]}",
                consumer_id=str(request.user.id),
            )
            c = result["commission_details"]
            deal.medusa_order_ext_id = uuid.UUID(new_order_ext_id)
            deal.medusa_service_ext_id = uuid.UUID(result["serviceExtId"])
            deal.medusa_payment_url = result["paymentUrl"]
            deal.medusa_order_status = "created"
            deal.medusa_platform_commission = c["platform_commission"]
            deal.medusa_tochka_commission = c["medusa_commission"]
            deal.medusa_acquiring_commission = c["acquiring_commission"]
            deal.medusa_total_commission = c["total_commission"]
            deal.medusa_total_amount = c["total_amount"]
            deal.medusa_recipient_ext_id = uuid.UUID(worker_data["recipient_ext_id"])
            deal.medusa_card_ext_id = uuid.UUID(worker_data["card_ext_id"])
            deal.save()

            # ✅ КЛЮЧЕВОЕ: обновляем deal_card в чате через WebSocket.
            # Это: (1) обновит сохранённое сообщение в БД с новыми deal_data,
            #      (2) разошлёт deal_card_updated всем участникам чата.
            # Фронт мгновенно увидит medusa_payment_url и переключит кнопки.
            try:
                from .services import DealService
                DealService._send_deal_card(deal, str(request.user.id), "payment_link_created", _auth_token(request))
            except Exception as e:
                logger.error("[Medusa] _send_deal_card after create error: %s", e)

            return Response({"status": "success", "data": {
                "payment_url": result["paymentUrl"],
                "total_amount": str(c["total_amount"]),
                "commission_details": {k: str(v) for k, v in c.items()},
            }})
        except MedusaAPIError as e:
            return Response({"status": "error", "error": f"Ошибка банка: {str(e)[:200]}"}, status=502)


class MedusaPaymentStatusView(APIView):
    """
    GET /api/market/medusa/payment-status/<deal_id>/

    Запрашивает Get Order V2 у Точки и переводит сделку в paid,
    если банк подтвердил оплату.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, deal_id):
        try:
            deal = Deal.objects.get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Не найдена"}, status=404)

        if str(request.user.id) not in [str(deal.client_id), str(deal.worker_id)]:
            return Response({"status": "error", "error": "Нет доступа"}, status=403)

        # Сделка уже оплачена — отвечаем сразу
        if deal.status != "pending":
            return Response({"status": "success", "data": {
                "medusa_status": deal.medusa_order_status or "unknown",
                "deal_status": deal.status,
                "message": "Сделка не в ожидании оплаты",
            }})

        if not deal.medusa_order_ext_id:
            return Response({"status": "success", "data": {
                "medusa_status": None,
                "deal_status": deal.status,
                "message": "Платёж ещё не создан",
            }})

        try:
            order_data = MedusaService().get_order(str(deal.medusa_order_ext_id))
        except MedusaAPIError as e:
            logger.error("[Medusa] get_order failed for deal=%s: %s", deal.id, e)
            return Response({"status": "success", "data": {
                "medusa_status": deal.medusa_order_status,
                "deal_status": deal.status,
                "message": "Не удалось получить статус от банка, попробуйте позже",
            }})

        state = (order_data.get("state") or order_data.get("status") or "").lower()
        logger.info("[Medusa] Order %s state=%s (deal=%s)", deal.medusa_order_ext_id, state, deal.id)

        deal.medusa_order_status = state or "unknown"

        # Оплачено
        if state in PAID_STATES:
            from .services import DealService
            from .models import Transaction

            if not deal.transactions.filter(status__in=["held", "captured"]).exists():
                Transaction.objects.create(
                    deal=deal,
                    amount=deal.price,
                    commission=deal.medusa_total_commission or 0,
                    status="held",
                    payment_provider="tochka_medusa",
                    external_payment_id=str(deal.medusa_order_ext_id),
                )

            deal.status = "paid"
            deal.paid_at = timezone.now()
            deal.save()

            token = _auth_token(request)
            try:
                DealService._send_text_message(
                    str(deal.chat_room_id),
                    str(deal.client_id),
                    f"💳 ЗАКАЗ ОПЛАЧЕН\n\nСумма: {int(deal.price)}₽\nСредства заморожены в банке до завершения работы.",
                    token,
                )
                DealService._send_deal_card(deal, str(deal.client_id), "paid", token)
            except Exception as e:
                logger.error("[Medusa] Notify chat error: %s", e)

            return Response({"status": "success", "data": {
                "medusa_status": state,
                "deal_status": deal.status,
                "message": "Оплата прошла успешно!",
            }})

        # Отменено / ошибка
        if state in CANCELED_STATES:
            deal.save(update_fields=["medusa_order_status"])
            return Response({"status": "success", "data": {
                "medusa_status": state,
                "deal_status": deal.status,
                "message": "Платёж отменён",
            }})

        # Ещё ждём оплату
        deal.save(update_fields=["medusa_order_status"])
        return Response({"status": "success", "data": {
            "medusa_status": state or "unknown",
            "deal_status": deal.status,
            "message": "Оплата ещё не поступила",
        }})


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
            return Response({"status": "error", "error": "Только после сдачи"}, status=400)
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
            return Response({"status": "error", "error": f"Ошибка банка: {str(e)[:200]}"}, status=502)


class MedusaRejectDealView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, deal_id):
        try:
            deal = Deal.objects.select_for_update().get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Не найдена"}, status=404)
        if str(request.user.id) not in [str(deal.client_id), str(deal.worker_id)]:
            return Response({"status": "error", "error": "Нет доступа"}, status=403)
        if not deal.medusa_order_ext_id or not deal.medusa_service_ext_id:
            return Response({"status": "error", "error": "Нет данных"}, status=400)
        try:
            medusa = MedusaService()
            medusa.make_decision(str(deal.medusa_order_ext_id), str(deal.medusa_service_ext_id), "rejected")
            medusa.sandbox_full_cycle_after_decision(str(deal.medusa_order_ext_id), str(deal.medusa_service_ext_id), "rejected")
            deal.medusa_order_status = "cancelled"
            deal.save(update_fields=["medusa_order_status"])
            return Response({"status": "success", "message": "Деньги возвращаются заказчику"})
        except MedusaAPIError as e:
            return Response({"status": "error", "error": f"Ошибка банка: {str(e)[:200]}"}, status=502)


class MedusaCalculateCommissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        price_str = request.query_params.get("price")
        if not price_str:
            return Response({"status": "error", "error": "price обязателен"}, status=400)
        try:
            price = Decimal(str(price_str))
            if price <= 0:
                raise ValueError
        except (ValueError, Exception):
            return Response({"status": "error", "error": "Некорректная цена"}, status=400)
        c = MedusaService.calculate_commission(price)
        return Response({"status": "success", "data": {k: str(v) for k, v in c.items()}})
