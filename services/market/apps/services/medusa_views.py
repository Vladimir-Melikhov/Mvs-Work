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
    """Получить профиль текущего пользователя из auth-сервиса."""
    token = _get_auth_token(request)
    try:
        resp = http_requests.get(
            f"{AUTH_SERVICE_URL}/api/auth/profile/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("data", {})
        logger.warning("[Medusa] _get_worker_profile: auth вернул %s", resp.status_code)
    except Exception as e:
        logger.error("[Medusa] Ошибка получения профиля: %s", e)
    return {}


def _update_worker_profile(request, fields: dict) -> bool:
    """Обновить поля профиля через auth-сервис (PATCH /api/auth/profile/)."""
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
        if resp.status_code == 200:
            return True
        logger.warning("[Medusa] _update_worker_profile: auth вернул %s: %s", resp.status_code, resp.text[:200])
        return False
    except Exception as e:
        logger.error("[Medusa] Ошибка обновления профиля: %s", e)
        return False


def _get_worker_medusa_data(worker_id: str) -> Optional[Dict[str, Any]]:
    """
    Получить recipient_ext_id и card_ext_id воркера из auth-сервиса.
    Используется при создании платежа (клиент оплачивает заказ).
    """
    from .jwt_service import ServiceJWT
    try:
        token = ServiceJWT.generate_service_token("market-medusa", expires_minutes=5)
        resp = http_requests.get(
            f"{AUTH_SERVICE_URL}/api/auth/internal/users/{worker_id}/profile/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if resp.status_code != 200:
            logger.warning("[Medusa] _get_worker_medusa_data: auth вернул %s для воркера %s", resp.status_code, worker_id)
            return None

        data = resp.json().get("data", {})
        profile = data.get("profile", {})

        recipient_ext_id = profile.get("medusa_recipient_ext_id")
        card_ext_id = profile.get("medusa_card_ext_id")
        card_linked = profile.get("medusa_card_linked", False)

        if not recipient_ext_id or not card_ext_id or not card_linked:
            logger.info(
                "[Medusa] Воркер %s не настроил карту: recipient=%s card=%s linked=%s",
                worker_id, recipient_ext_id, card_ext_id, card_linked,
            )
            return None

        return {
            "recipient_ext_id": str(recipient_ext_id),
            "card_ext_id": str(card_ext_id),
        }
    except Exception as e:
        logger.error("[Medusa] Ошибка получения данных воркера %s: %s", worker_id, e)
        return None


# ─── Регистрация получателя ───────────────────────────────────────────────────

class MedusaRegisterRecipientView(APIView):
    """
    Шаг 1: Зарегистрировать воркера как получателя выплат в Medusa.
    Вызывается один раз. При повторном вызове возвращает уже сохранённый ext_id.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        profile = _get_worker_profile(request)
        if not profile:
            return Response({"status": "error", "error": "Не удалось получить профиль"}, status=400)

        p = profile.get("profile", {})

        # Если уже зарегистрированы — возвращаем сохранённый ext_id
        existing_ext_id = p.get("medusa_recipient_ext_id")
        if existing_ext_id or p.get("medusa_recipient_registered"):
            ext_id = existing_ext_id or str(request.user.id)
            logger.info("[Medusa] Воркер %s уже зарегистрирован как получатель", request.user.id)
            return Response({
                "status": "success",
                "data": {
                    "recipient_ext_id": ext_id,
                    "message": "Вы уже зарегистрированы как получатель. Привяжите карту."
                }
            })

        # Используем UUID пользователя как extId получателя
        recipient_ext_id = str(request.user.id)
        worker_name = (
            p.get("full_name")
            or p.get("company_name")
            or profile.get("email", "Worker")
        )

        try:
            medusa = MedusaService()
            medusa.create_recipient(recipient_ext_id, worker_name)

            # Сохраняем в профиль
            _update_worker_profile(request, {
                "medusa_recipient_ext_id": recipient_ext_id,
                "medusa_recipient_registered": True,
            })

            logger.info("[Medusa] ✅ Получатель зарегистрирован: %s (%s)", recipient_ext_id, worker_name)
            return Response({
                "status": "success",
                "data": {
                    "recipient_ext_id": recipient_ext_id,
                    "name": worker_name,
                    "message": "Зарегистрированы как получатель. Теперь привяжите карту.",
                }
            })

        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка регистрации получателя: HTTP %s — %s", e.status_code, e)

            # Если получатель уже существует в Tochka (4xx кроме 404) — пробуем получить его
            if e.status_code and e.status_code not in (404, 0):
                try:
                    medusa_check = MedusaService()
                    existing = medusa_check.get_recipient(recipient_ext_id)
                    if existing.get("extId"):
                        _update_worker_profile(request, {
                            "medusa_recipient_ext_id": recipient_ext_id,
                            "medusa_recipient_registered": True,
                        })
                        logger.info("[Medusa] Получатель уже существует в Tochka, обновили профиль")
                        return Response({
                            "status": "success",
                            "data": {
                                "recipient_ext_id": recipient_ext_id,
                                "message": "Зарегистрированы. Привяжите карту.",
                            }
                        })
                except Exception as check_err:
                    logger.warning("[Medusa] Не удалось проверить существование получателя: %s", check_err)

            return Response({
                "status": "error",
                "error": f"Ошибка банка (HTTP {e.status_code}): {e}",
            }, status=502)


# ─── Привязка карты ───────────────────────────────────────────────────────────

class MedusaAddCardView(APIView):
    """
    Шаг 2: Получить ссылку на форму Tochka для ввода данных карты.
    Карта считается привязанной только ПОСЛЕ того, как пользователь
    прошёл форму и `MedusaRecipientInfoView` подтвердил наличие карты через Tochka.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        # Проверяем, что получатель зарегистрирован
        profile = _get_worker_profile(request)
        p = profile.get("profile", {})

        if not p.get("medusa_recipient_registered"):
            return Response({
                "status": "error",
                "error": "Сначала зарегистрируйтесь как получатель",
                "action_required": "register_recipient",
            }, status=400)

        recipient_ext_id = str(request.user.id)
        frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")
        redirect_url = request.data.get(
            "redirect_url",
            f"{frontend_url}/profile?card=linked"
        )

        # UUID для метода выплаты — сохраним в профиль сразу,
        # но медика_card_linked установим только после подтверждения через get_recipient
        payout_method_ext_id = str(uuid.uuid4())

        try:
            medusa = MedusaService()
            result = medusa.add_card_payout_method(
                recipient_ext_id=recipient_ext_id,
                redirect_url=redirect_url,
                payout_method_ext_id=payout_method_ext_id,
            )

            # Сохраняем ext_id карты, но НЕ ставим card_linked=True — это сделает
            # MedusaRecipientInfoView после того, как пользователь вернётся и
            # нажмёт «Обновить» (реальная проверка через get_recipient)
            _update_worker_profile(request, {
                "medusa_card_ext_id": result["payoutMethodExtId"],
                "medusa_card_linked": False,          # будет True после подтверждения
                "medusa_card_masked_pan": None,        # обновится после подтверждения
            })

            logger.info(
                "[Medusa] ✅ Форма привязки карты выдана воркеру %s, payout_method_ext_id=%s",
                request.user.id, result["payoutMethodExtId"],
            )

            return Response({
                "status": "success",
                "data": {
                    "form_url": result["formUrl"],
                    "payout_method_ext_id": result["payoutMethodExtId"],
                    "message": "Перейдите по ссылке для ввода данных карты. После завершения вернитесь и нажмите «Обновить».",
                },
            })

        except MedusaAPIError as e:
            logger.error(
                "[Medusa] Ошибка add_card для воркера %s: HTTP %s — %s",
                request.user.id, e.status_code, e,
            )

            if e.status_code == 404:
                # Получатель не найден в Tochka — нужно перерегистрироваться
                _update_worker_profile(request, {
                    "medusa_recipient_registered": False,
                    "medusa_recipient_ext_id": None,
                })
                return Response({
                    "status": "error",
                    "error": "Получатель не найден в системе банка. Пожалуйста, зарегистрируйтесь заново.",
                    "action_required": "register_recipient",
                }, status=400)

            if e.status_code == 403:
                return Response({
                    "status": "error",
                    "error": "Ошибка авторизации в банке. Проверьте настройки MEDUSA_SIGN_KEY_ID и MEDUSA_SIGN_BODY.",
                }, status=502)

            return Response({
                "status": "error",
                "error": f"Ошибка банка (HTTP {e.status_code}): {e}",
            }, status=502)


# ─── Информация о получателе (синхронизация с Tochka) ────────────────────────

class MedusaRecipientInfoView(APIView):
    """
    Получить актуальную информацию о получателе и его картах.
    При наличии recipient_ext_id вызывает Tochka для получения свежих данных.
    Используется кнопкой «Обновить» в профиле после привязки карты.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        profile = _get_worker_profile(request)
        p = profile.get("profile", {})

        registered = bool(p.get("medusa_recipient_registered"))
        card_linked = bool(p.get("medusa_card_linked"))
        cards = []

        # Если зарегистрированы — синхронизируемся с Tochka
        if registered:
            try:
                medusa = MedusaService()
                recipient_data = medusa.get_recipient(str(request.user.id))
                payout_methods = recipient_data.get("PayoutMethods") or []

                if payout_methods:
                    card_linked = True
                    for method in payout_methods:
                        cards.append({
                            "ext_id": method.get("extId", ""),
                            "masked_pan": method.get("maskedCardNumber", "****"),
                            "type": method.get("methodType", "CARD"),
                        })

                    # Обновляем профиль с актуальными данными карты
                    first_card = payout_methods[0]
                    _update_worker_profile(request, {
                        "medusa_card_ext_id": first_card.get("extId"),
                        "medusa_card_linked": True,
                        "medusa_card_masked_pan": first_card.get("maskedCardNumber", "****"),
                    })
                    logger.info("[Medusa] ✅ Карта подтверждена для воркера %s", request.user.id)
                else:
                    # Карт нет — обновляем статус, если был ложно-положительный
                    if card_linked:
                        _update_worker_profile(request, {"medusa_card_linked": False})
                        card_linked = False
                        logger.info("[Medusa] Карта ещё не привязана для воркера %s", request.user.id)

            except MedusaAPIError as e:
                logger.warning("[Medusa] Не удалось получить данные получателя: HTTP %s — %s", e.status_code, e)
                # Используем локальные данные
                if p.get("medusa_card_ext_id"):
                    card_linked = bool(p.get("medusa_card_linked"))
                    if card_linked:
                        cards = [{
                            "ext_id": str(p["medusa_card_ext_id"]),
                            "masked_pan": p.get("medusa_card_masked_pan") or "****",
                            "type": "CARD",
                        }]
            except Exception as e:
                logger.error("[Medusa] Неожиданная ошибка при синхронизации: %s", e)

        return Response({
            "status": "success",
            "data": {
                "recipient_ext_id": str(p["medusa_recipient_ext_id"]) if p.get("medusa_recipient_ext_id") else None,
                "name": p.get("full_name") or p.get("company_name") or "",
                "cards": cards,
                "has_card": card_linked,
                "registered": registered,
            },
        })


# ─── Удаление карты ───────────────────────────────────────────────────────────

class MedusaDeleteCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response({"status": "error", "error": "Только для исполнителей"}, status=403)

        payout_method_ext_id = request.data.get("payout_method_ext_id")
        if not payout_method_ext_id:
            return Response({"status": "error", "error": "payout_method_ext_id обязателен"}, status=400)

        try:
            medusa = MedusaService()
            medusa.delete_card_payout_method(str(request.user.id), payout_method_ext_id)
            logger.info("[Medusa] Карта %s удалена для воркера %s", payout_method_ext_id, request.user.id)
        except MedusaAPIError as e:
            logger.warning("[Medusa] Ошибка удаления карты %s: %s", payout_method_ext_id, e)
            # Даже при ошибке Tochka — сбрасываем локальные данные

        _update_worker_profile(request, {
            "medusa_card_ext_id": None,
            "medusa_card_masked_pan": None,
            "medusa_card_linked": False,
        })

        return Response({"status": "success", "message": "Карта удалена"})


# ─── Создание платежа ─────────────────────────────────────────────────────────

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

        # Если ссылка уже создана — отдаём её
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
                }
            })

        # Получаем данные карты воркера
        worker_profile = _get_worker_medusa_data(str(deal.worker_id))
        if not worker_profile:
            return Response({
                "status": "error",
                "error": "Исполнитель ещё не привязал карту для выплат. "
                         "Попросите исполнителя зайти в профиль → «Безопасные сделки» и привязать карту.",
                "action_required": "worker_card_required",
            }, status=400)

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

            logger.info(
                "[Medusa] ✅ Платёж создан для сделки %s, сумма=%s₽",
                deal.id, c["total_amount"],
            )

            return Response({
                "status": "success",
                "data": {
                    "payment_url": result["paymentUrl"],
                    "total_amount": str(c["total_amount"]),
                    "service_price": str(deal.price),
                    "commission_details": {
                        "platform": str(c["platform_commission"]),
                        "tochka": str(c["medusa_commission"]),
                        "acquiring": str(c["acquiring_commission"]),
                        "total": str(c["total_commission"]),
                    },
                    "message": "Перейдите по ссылке для оплаты",
                }
            })

        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка создания заказа для сделки %s: HTTP %s — %s", deal.id, e.status_code, e)
            return Response({
                "status": "error",
                "error": f"Ошибка платёжного сервиса (HTTP {e.status_code}): {e}",
            }, status=502)


# ─── Статус платежа ───────────────────────────────────────────────────────────

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
            return Response({
                "status": "success",
                "data": {
                    "medusa_status": None,
                    "deal_status": deal.status,
                    "message": "Заказ не создан в платёжной системе",
                }
            })

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
                DealService._send_text_message(
                    chat_room_id=str(deal.chat_room_id),
                    sender_id=str(deal.client_id),
                    text=(
                        f"💳 ЗАКАЗ ОПЛАЧЕН\n\nСумма: {int(deal.price)}₽\n"
                        f"Комиссия: {deal.medusa_total_commission}₽\n"
                        f"Итого: {deal.medusa_total_amount}₽\n\nДеньги заморожены."
                    ),
                    auth_token=token,
                )
                DealService._send_deal_card(deal, str(deal.client_id), "paid", token)
            else:
                deal.save(update_fields=["medusa_order_status"])

            return Response({
                "status": "success",
                "data": {
                    "medusa_status": medusa_status,
                    "deal_status": deal.status,
                    "total_amount": str(deal.medusa_total_amount) if deal.medusa_total_amount else None,
                    "message": self._msg(medusa_status),
                }
            })

        except MedusaAPIError as e:
            logger.warning("[Medusa] Ошибка получения статуса заказа %s: %s", deal.medusa_order_ext_id, e)
            return Response({
                "status": "success",
                "data": {
                    "medusa_status": deal.medusa_order_status,
                    "deal_status": deal.status,
                    "message": "Статус из локальной БД",
                }
            })

    @staticmethod
    def _msg(s):
        return {
            "waiting_user_payment": "Ожидает оплаты",
            "waiting_enroll": "Зачисление",
            "waiting_services": "Оплачено, средства заморожены",
            "finished": "Завершено",
            "canceled": "Отменён",
        }.get(s, f"Статус: {s}")


# ─── Подтверждение выплаты (клиент принимает работу) ─────────────────────────

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
            medusa.sandbox_full_cycle_after_decision(
                str(deal.medusa_order_ext_id),
                str(deal.medusa_service_ext_id),
                "confirmed",
            )
            deal.medusa_order_status = "completed"
            deal.save(update_fields=["medusa_order_status"])
            logger.info("[Medusa] ✅ Выплата подтверждена для сделки %s", deal_id)
            return Response({"status": "success", "message": "Деньги выплачиваются исполнителю"})
        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка confirm для сделки %s: HTTP %s — %s", deal_id, e.status_code, e)
            return Response({"status": "error", "error": f"Ошибка: {e}"}, status=502)


# ─── Отклонение (возврат средств) ────────────────────────────────────────────

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
            medusa.sandbox_full_cycle_after_decision(
                str(deal.medusa_order_ext_id),
                str(deal.medusa_service_ext_id),
                "rejected",
            )
            deal.medusa_order_status = "cancelled"
            deal.save(update_fields=["medusa_order_status"])
            logger.info("[Medusa] ✅ Возврат инициирован для сделки %s", deal_id)
            return Response({"status": "success", "message": "Деньги возвращаются заказчику"})
        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка reject для сделки %s: HTTP %s — %s", deal_id, e.status_code, e)
            return Response({"status": "error", "error": f"Ошибка: {e}"}, status=502)


# ─── Расчёт комиссий ──────────────────────────────────────────────────────────

class MedusaCalculateCommissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        price = request.query_params.get("price")
        if not price:
            return Response({"status": "error", "error": "price обязателен"}, status=400)

        try:
            p = Decimal(str(price))
            if p <= 0:
                raise ValueError("price must be positive")
        except (ValueError, Exception):
            return Response({"status": "error", "error": "Некорректная цена"}, status=400)

        c = MedusaService.calculate_commission(p)
        return Response({
            "status": "success",
            "data": {
                "service_price": str(c["service_price"]),
                "platform_commission": str(c["platform_commission"]),
                "medusa_commission": str(c["medusa_commission"]),
                "acquiring_commission": str(c["acquiring_commission"]),
                "total_commission": str(c["total_commission"]),
                "total_amount": str(c["total_amount"]),
                "commission_rate_total": "3.50",
            }
        })
