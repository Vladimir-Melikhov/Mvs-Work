"""
services/market/apps/services/medusa_views.py

Views для работы с Безопасными сделками Tochka Bank (Medusa).

Простой флоу:

1. Воркер регистрируется как получатель:
   POST /api/market/medusa/register-recipient/

2. Воркер привязывает карту (форма открывается в новой вкладке):
   POST /api/market/medusa/add-card/

3. Воркер возвращается, нажимает «Обновить» — проверяем через Tochka есть ли карта:
   GET  /api/market/medusa/recipient-info/

4. Клиент оплачивает сделку:
   POST /api/market/medusa/create-payment/

5. Клиент подтверждает работу (выплата) или отклоняет (возврат):
   POST /api/market/medusa/confirm-deal/<deal_id>/
   POST /api/market/medusa/reject-deal/<deal_id>/
"""
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


# ─── Вспомогательные функции ─────────────────────────────────────────────────

def _auth_token(request) -> str:
    """Извлечь bearer-токен из заголовка Authorization"""
    h = request.headers.get("Authorization", "")
    return h.split(" ", 1)[1] if h.startswith("Bearer ") else ""


def _get_my_profile(request) -> dict:
    """Получить свой профиль из auth-сервиса (с medusa_* полями)"""
    token = _auth_token(request)
    try:
        r = http_requests.get(
            f"{AUTH_SERVICE_URL}/api/auth/profile/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if r.status_code == 200:
            return r.json().get("data", {})
        logger.warning("[Medusa] profile GET вернул %s: %s", r.status_code, r.text[:200])
    except Exception as e:
        logger.error("[Medusa] Ошибка получения профиля: %s", e)
    return {}


def _patch_my_profile(request, fields: dict) -> bool:
    """
    Обновить свой профиль через auth-сервис.
    Поля medusa_* — пробрасываются напрямую в модель Profile.
    """
    token = _auth_token(request)
    try:
        r = http_requests.patch(
            f"{AUTH_SERVICE_URL}/api/auth/profile/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=fields,
            timeout=5,
        )
        if r.status_code == 200:
            return True
        logger.warning("[Medusa] profile PATCH вернул %s: %s", r.status_code, r.text[:300])
    except Exception as e:
        logger.error("[Medusa] Ошибка PATCH профиля: %s", e)
    return False


def _get_worker_medusa_data(worker_id: str) -> Optional[Dict[str, str]]:
    """
    Получить recipient_ext_id и card_ext_id воркера (для создания платежа).
    Используется межсервисный JWT.
    """
    from .jwt_service import ServiceJWT
    try:
        token = ServiceJWT.generate_service_token("market-medusa", expires_minutes=5)
        url = f"{AUTH_SERVICE_URL}/api/auth/internal/users/{worker_id}/profile/"
        logger.info("[Medusa] _get_worker_medusa_data: GET %s", url)

        r = http_requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if r.status_code != 200:
            logger.warning(
                "[Medusa] internal profile для %s вернул %s: %s",
                worker_id, r.status_code, r.text[:300],
            )
            return None

        data = r.json().get("data", {})
        p = data.get("profile", {})

        recipient_id = p.get("medusa_recipient_ext_id")
        card_id = p.get("medusa_card_ext_id")
        linked = p.get("medusa_card_linked", False)

        logger.info(
            "[Medusa] Воркер %s: recipient=%s card=%s linked=%s (все medusa_* поля в ответе: %s)",
            worker_id, recipient_id, card_id, linked,
            {k: v for k, v in p.items() if str(k).startswith("medusa")},
        )

        if not recipient_id or not card_id or not linked:
            return None

        return {
            "recipient_ext_id": str(recipient_id),
            "card_ext_id": str(card_id),
        }
    except Exception as e:
        logger.error(
            "[Medusa] Ошибка получения данных воркера %s: %s",
            worker_id, e, exc_info=True,
        )
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Шаг 1: Регистрация воркера как получателя
# ═══════════════════════════════════════════════════════════════════════════

class MedusaRegisterRecipientView(APIView):
    """
    POST /api/market/medusa/register-recipient/
    
    Регистрирует воркера как получателя выплат в Tochka.
    Вызывается один раз перед привязкой карты.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response(
                {"status": "error", "error": "Только для исполнителей"},
                status=403,
            )

        profile_data = _get_my_profile(request)
        if not profile_data:
            return Response(
                {"status": "error", "error": "Не удалось получить профиль"},
                status=500,
            )

        p = profile_data.get("profile", {})

        # Если уже зарегистрирован — просто возвращаем успех
        if p.get("medusa_recipient_registered") and p.get("medusa_recipient_ext_id"):
            return Response({
                "status": "success",
                "data": {
                    "recipient_ext_id": str(p["medusa_recipient_ext_id"]),
                    "message": "Уже зарегистрированы. Теперь привяжите карту.",
                }
            })

        # extId = UUID пользователя (стабильный, уникальный)
        recipient_ext_id = str(request.user.id)
        name = (
            p.get("full_name")
            or p.get("company_name")
            or profile_data.get("email", "Worker")
        )

        try:
            medusa = MedusaService()
            medusa.create_recipient(recipient_ext_id, name)

            # Сохраняем в профиль
            ok = _patch_my_profile(request, {
                "medusa_recipient_ext_id": recipient_ext_id,
                "medusa_recipient_registered": True,
            })

            if not ok:
                logger.error("[Medusa] Не удалось сохранить recipient_ext_id в профиле")

            return Response({
                "status": "success",
                "data": {
                    "recipient_ext_id": recipient_ext_id,
                    "message": "Успешная регистрация! Теперь привяжите карту.",
                }
            })

        except MedusaAPIError as e:
            logger.error("[Medusa] create_recipient ошибка: HTTP %s — %s", e.status_code, e)

            # Возможно, получатель уже существует в Tochka — проверяем через GET
            try:
                existing = medusa.get_recipient(recipient_ext_id)
                if existing and existing.get("extId"):
                    _patch_my_profile(request, {
                        "medusa_recipient_ext_id": recipient_ext_id,
                        "medusa_recipient_registered": True,
                    })
                    return Response({
                        "status": "success",
                        "data": {
                            "recipient_ext_id": recipient_ext_id,
                            "message": "Регистрация восстановлена.",
                        }
                    })
            except Exception:
                pass

            return Response({
                "status": "error",
                "error": f"Ошибка банка: HTTP {e.status_code}. {str(e)[:200]}",
            }, status=502)


# ═══════════════════════════════════════════════════════════════════════════
# Шаг 2: Привязка карты — получение ссылки на форму
# ═══════════════════════════════════════════════════════════════════════════

class MedusaAddCardView(APIView):
    """
    POST /api/market/medusa/add-card/
    
    Возвращает ссылку на форму Tochka для ввода данных карты.
    После заполнения карта привязывается автоматически — воркер вернётся
    и увидит привязанную карту (после нажатия «Обновить»).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "worker":
            return Response(
                {"status": "error", "error": "Только для исполнителей"},
                status=403,
            )

        profile_data = _get_my_profile(request)
        p = profile_data.get("profile", {})

        # Проверяем что получатель зарегистрирован
        if not p.get("medusa_recipient_registered") or not p.get("medusa_recipient_ext_id"):
            return Response({
                "status": "error",
                "error": "Сначала нужно зарегистрироваться как получатель",
                "action_required": "register_recipient",
            }, status=400)

        recipient_ext_id = str(p["medusa_recipient_ext_id"])

        frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")
        redirect_url = request.data.get(
            "redirect_url",
            f"{frontend_url}/profile?card_added=1",
        )

        # Генерируем новый UUID для этой карты
        payout_method_ext_id = str(uuid.uuid4())

        try:
            medusa = MedusaService()
            result = medusa.add_card_payout_method(
                recipient_ext_id=recipient_ext_id,
                redirect_url=redirect_url,
                payout_method_ext_id=payout_method_ext_id,
            )

            # Сохраняем payout_method_ext_id, но linked=False
            # (станет True после того, как пользователь реально привяжет карту
            # и мы это подтвердим через get_recipient)
            _patch_my_profile(request, {
                "medusa_card_ext_id": payout_method_ext_id,
                "medusa_card_linked": False,
                "medusa_card_masked_pan": None,
            })

            return Response({
                "status": "success",
                "data": {
                    "form_url": result["formUrl"],
                    "payout_method_ext_id": payout_method_ext_id,
                    "message": "Перейдите по ссылке для ввода данных карты",
                }
            })

        except MedusaAPIError as e:
            logger.error(
                "[Medusa] add_card ошибка: HTTP %s — %s (recipient=%s)",
                e.status_code, e, recipient_ext_id,
            )

            # 404 — получатель не найден в Tochka (может удалили на их стороне)
            if e.status_code == 404:
                _patch_my_profile(request, {
                    "medusa_recipient_registered": False,
                })
                return Response({
                    "status": "error",
                    "error": "Получатель не найден в банке. Зарегистрируйтесь заново.",
                    "action_required": "register_recipient",
                }, status=400)

            return Response({
                "status": "error",
                "error": f"Ошибка банка: HTTP {e.status_code}. {str(e)[:200]}",
            }, status=502)


# ═══════════════════════════════════════════════════════════════════════════
# Синхронизация с Tochka — обновление информации о карте
# ═══════════════════════════════════════════════════════════════════════════

class MedusaRecipientInfoView(APIView):
    """
    GET /api/market/medusa/recipient-info/
    
    Синхронизирует данные карты с Tochka.
    Вызывается при открытии профиля и по кнопке «Обновить» после привязки карты.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "worker":
            return Response(
                {"status": "error", "error": "Только для исполнителей"},
                status=403,
            )

        profile_data = _get_my_profile(request)
        p = profile_data.get("profile", {})

        registered = bool(p.get("medusa_recipient_registered"))
        recipient_ext_id = p.get("medusa_recipient_ext_id")

        response_data = {
            "recipient_ext_id": str(recipient_ext_id) if recipient_ext_id else None,
            "registered": registered,
            "name": p.get("full_name") or p.get("company_name") or "",
            "has_card": False,
            "cards": [],
            # Дублируем card_ext_id из профиля на верхний уровень — чтобы фронт мог
            # удалить карту даже если cards[] пустой (например, после Force-link
            # на stage, когда Tochka карту не вернула в PayoutMethods).
            "card_ext_id": str(p["medusa_card_ext_id"]) if p.get("medusa_card_ext_id") else None,
            "card_masked_pan": p.get("medusa_card_masked_pan"),
            "card_linked": bool(p.get("medusa_card_linked")),
        }

        # Если не зарегистрирован — возвращаем как есть
        if not registered or not recipient_ext_id:
            return Response({"status": "success", "data": response_data})

        # Синхронизируемся с Tochka
        try:
            medusa = MedusaService()
            recipient_data = medusa.get_recipient(str(recipient_ext_id))
            payout_methods = recipient_data.get("PayoutMethods") or []

            # ДИАГНОСТИКА: логируем всё что пришло от Точки
            logger.info(
                "[Medusa] recipient_data для %s: PayoutMethods count=%d, raw=%s",
                recipient_ext_id, len(payout_methods), payout_methods,
            )

            # Фильтруем только карты (не SBP)
            cards = [
                m for m in payout_methods
                if m.get("methodType", "").upper() in ("CARD", "CARD_PAYOUT_METHOD")
            ]

            # Если API не различает типы — берём все
            if not cards and payout_methods:
                cards = payout_methods

            if cards:
                # Берём первую карту как основную
                main_card = cards[0]
                card_ext_id = main_card.get("extId", "")
                masked_pan = main_card.get("maskedCardNumber", "****")

                # PATCH только если что-то реально изменилось (избегаем rate limit)
                current_linked = bool(p.get("medusa_card_linked"))
                current_card_id = str(p.get("medusa_card_ext_id") or "")
                current_pan = p.get("medusa_card_masked_pan") or ""

                needs_update = (
                    not current_linked
                    or current_card_id != card_ext_id
                    or current_pan != masked_pan
                )

                if needs_update:
                    _patch_my_profile(request, {
                        "medusa_card_ext_id": card_ext_id,
                        "medusa_card_linked": True,
                        "medusa_card_masked_pan": masked_pan,
                    })
                    logger.info(
                        "[Medusa] ✅ Карта подтверждена для воркера %s: %s",
                        request.user.id, masked_pan,
                    )

                response_data["has_card"] = True
                response_data["cards"] = [
                    {
                        "ext_id": c.get("extId", ""),
                        "masked_pan": c.get("maskedCardNumber", "****"),
                        "type": c.get("methodType", "CARD"),
                    }
                    for c in cards
                ]
            else:
                # Карт нет — сбрасываем статус ТОЛЬКО если он был true
                if p.get("medusa_card_linked"):
                    _patch_my_profile(request, {
                        "medusa_card_linked": False,
                        "medusa_card_masked_pan": None,
                    })
                    logger.info("[Medusa] Карта сброшена для воркера %s", request.user.id)

        except MedusaAPIError as e:
            logger.warning(
                "[Medusa] get_recipient ошибка: HTTP %s — %s",
                e.status_code, e,
            )
            # При ошибке Tochka — используем данные из локального профиля
            if p.get("medusa_card_linked") and p.get("medusa_card_ext_id"):
                response_data["has_card"] = True
                response_data["cards"] = [{
                    "ext_id": str(p["medusa_card_ext_id"]),
                    "masked_pan": p.get("medusa_card_masked_pan") or "****",
                    "type": "CARD",
                }]

        except Exception as e:
            logger.error("[Medusa] recipient-info неожиданная ошибка: %s", e)

        return Response({"status": "success", "data": response_data})


# ═══════════════════════════════════════════════════════════════════════════
# Удаление карты
# ═══════════════════════════════════════════════════════════════════════════

class MedusaDeleteCardView(APIView):
    """POST /api/market/medusa/delete-card/"""
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

        # Пытаемся удалить в Tochka (даже если не получится — сбросим локально)
        try:
            medusa = MedusaService()
            medusa.delete_card_payout_method(
                str(request.user.id),
                payout_method_ext_id,
            )
        except Exception as e:
            logger.warning("[Medusa] Ошибка удаления в Tochka: %s", e)

        # Сбрасываем локальные данные
        _patch_my_profile(request, {
            "medusa_card_ext_id": None,
            "medusa_card_masked_pan": None,
            "medusa_card_linked": False,
        })

        return Response({"status": "success", "message": "Карта удалена"})


# ═══════════════════════════════════════════════════════════════════════════
# ОТЛАДОЧНЫЕ ЭНДПОИНТЫ (только для stage!)
# ═══════════════════════════════════════════════════════════════════════════

class MedusaResetRecipientView(APIView):
    """
    POST /api/market/medusa/reset-recipient/
    
    ОТЛАДКА: полностью сбрасывает в профиле все medusa_* поля.
    Позволяет "начать заново" если получатель залип в странном состоянии.
    
    НЕ удаляет получателя в Tochka — только сбрасывает локальные ссылки.
    Доступен только на stage (MEDUSA_ENV=stage).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        is_stage = os.getenv("MEDUSA_ENV", "stage").lower() == "stage"
        if not is_stage:
            return Response(
                {"status": "error", "error": "Доступно только на stage"},
                status=403,
            )

        if request.user.role != "worker":
            return Response(
                {"status": "error", "error": "Только для исполнителей"},
                status=403,
            )

        _patch_my_profile(request, {
            "medusa_recipient_ext_id": None,
            "medusa_recipient_registered": False,
            "medusa_card_ext_id": None,
            "medusa_card_linked": False,
            "medusa_card_masked_pan": None,
        })

        logger.info("[Medusa] 🔄 Reset recipient для воркера %s", request.user.id)

        return Response({
            "status": "success",
            "message": "Данные получателя сброшены. Можете регистрироваться заново.",
        })


class MedusaForceLinkCardView(APIView):
    """
    POST /api/market/medusa/force-link-card/
    
    ОТЛАДКА: принудительно помечает карту как привязанную.
    Нужно для stage когда Точка не эмулирует фактическую привязку
    (форма показывается, но в PayoutMethods карта не появляется).
    
    Использует medusa_card_ext_id, который уже был сохранён при нажатии
    "Привязать карту" — то есть карта технически создана в Медузе,
    просто её нет в списке.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        is_stage = os.getenv("MEDUSA_ENV", "stage").lower() == "stage"
        if not is_stage:
            return Response(
                {"status": "error", "error": "Доступно только на stage"},
                status=403,
            )

        if request.user.role != "worker":
            return Response(
                {"status": "error", "error": "Только для исполнителей"},
                status=403,
            )

        profile_data = _get_my_profile(request)
        p = profile_data.get("profile", {})

        if not p.get("medusa_card_ext_id"):
            return Response(
                {"status": "error", "error": "Сначала нажмите «Привязать карту»"},
                status=400,
            )

        _patch_my_profile(request, {
            "medusa_card_linked": True,
            "medusa_card_masked_pan": p.get("medusa_card_masked_pan") or "4111****1111",
        })

        logger.info("[Medusa] 🔧 Force-link card для воркера %s", request.user.id)

        return Response({
            "status": "success",
            "message": "Карта помечена как привязанная (stage only)",
        })


# ═══════════════════════════════════════════════════════════════════════════
# Создание платежа клиентом
# ═══════════════════════════════════════════════════════════════════════════

class MedusaCreatePaymentView(APIView):
    """
    POST /api/market/medusa/create-payment/
    body: {"deal_id": "..."}
    
    Создаёт заказ в Medusa, возвращает paymentUrl.
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
            return Response({"status": "error", "error": "Сделка не найдена"}, status=404)

        if str(request.user.id) != str(deal.client_id):
            return Response(
                {"status": "error", "error": "Оплатить может только заказчик"},
                status=403,
            )

        if not deal.is_escrow:
            return Response(
                {"status": "error", "error": "Это не безопасная сделка"},
                status=400,
            )

        if deal.status != "pending":
            return Response({
                "status": "error",
                "error": f"Нельзя оплатить в статусе '{deal.status}'",
            }, status=400)

        # Если ссылка уже создана — возвращаем её
        if deal.medusa_payment_url and deal.medusa_order_ext_id:
            return Response({
                "status": "success",
                "data": {
                    "payment_url": deal.medusa_payment_url,
                    "total_amount": str(deal.medusa_total_amount or deal.price),
                    "commission_details": {
                        "platform": str(deal.medusa_platform_commission or 0),
                        "tochka": str(deal.medusa_tochka_commission or 0),
                        "acquiring": str(deal.medusa_acquiring_commission or 0),
                        "total": str(deal.medusa_total_commission or 0),
                    },
                    "message": "Ссылка на оплату уже создана",
                }
            })

        # Проверяем что воркер готов принимать оплату
        worker_data = _get_worker_medusa_data(str(deal.worker_id))
        if not worker_data:
            return Response({
                "status": "error",
                "error": "Исполнитель ещё не привязал карту для выплат. "
                         "Попросите его зайти в профиль → «Безопасные сделки».",
                "action_required": "worker_card_required",
            }, status=400)

        frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")

        try:
            medusa = MedusaService()
            result = medusa.create_order(
                order_ext_id=str(deal.id),
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

            # Сохраняем данные в сделку
            deal.medusa_order_ext_id = uuid.UUID(result["orderExtId"])
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

            return Response({
                "status": "success",
                "data": {
                    "payment_url": result["paymentUrl"],
                    "service_price": str(deal.price),
                    "total_amount": str(c["total_amount"]),
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
            logger.error("[Medusa] create_order ошибка: HTTP %s — %s", e.status_code, e)
            return Response({
                "status": "error",
                "error": f"Ошибка банка: HTTP {e.status_code}. {str(e)[:200]}",
            }, status=502)


# ═══════════════════════════════════════════════════════════════════════════
# Проверка статуса оплаты
# ═══════════════════════════════════════════════════════════════════════════

class MedusaPaymentStatusView(APIView):
    """
    GET /api/market/medusa/payment-status/<deal_id>/
    
    Проверяет статус заказа в Medusa. Если оплачен — обновляет статус сделки.
    """
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
                    "message": "Платёж не инициирован",
                }
            })

        # Запрашиваем актуальный статус в Tochka
        try:
            medusa = MedusaService()
            order_data = medusa.get_order(str(deal.medusa_order_ext_id))
            medusa_state = order_data.get("state") or "unknown"

            deal.medusa_order_status = medusa_state

            # Если деньги пришли и заморожены — переводим сделку в paid
            is_paid = medusa_state in (
                "waiting_services", "waiting_enroll", "paid",
                "waiting_compensation", "waiting_commissions", "finished",
            )

            if is_paid and deal.status == "pending":
                from .services import DealService
                deal.status = "paid"
                deal.paid_at = timezone.now()
                deal.save()

                token = _auth_token(request)
                DealService._send_text_message(
                    chat_room_id=str(deal.chat_room_id),
                    sender_id=str(deal.client_id),
                    text=(
                        f"💳 ЗАКАЗ ОПЛАЧЕН\n\n"
                        f"Сумма: {int(deal.price)}₽\n"
                        f"Комиссия: {deal.medusa_total_commission}₽\n"
                        f"Итого списано: {deal.medusa_total_amount}₽\n\n"
                        f"Средства заморожены до завершения сделки."
                    ),
                    auth_token=token,
                )
                DealService._send_deal_card(deal, str(deal.client_id), "paid", token)
            else:
                deal.save(update_fields=["medusa_order_status"])

            return Response({
                "status": "success",
                "data": {
                    "medusa_status": medusa_state,
                    "deal_status": deal.status,
                    "total_amount": str(deal.medusa_total_amount) if deal.medusa_total_amount else None,
                    "message": self._status_message(medusa_state),
                }
            })

        except MedusaAPIError as e:
            logger.warning("[Medusa] payment-status ошибка: %s", e)
            return Response({
                "status": "success",
                "data": {
                    "medusa_status": deal.medusa_order_status,
                    "deal_status": deal.status,
                    "message": "Используются локальные данные",
                }
            })

    @staticmethod
    def _status_message(state: str) -> str:
        return {
            "waiting_user_payment": "Ожидает оплаты",
            "waiting_enroll": "Зачисление",
            "waiting_services": "Оплачено, средства заморожены",
            "waiting_compensation": "Возврат",
            "waiting_commissions": "Обработка комиссий",
            "finished": "Завершено",
            "canceled": "Отменено",
        }.get(state, f"Статус: {state}")


# ═══════════════════════════════════════════════════════════════════════════
# Подтверждение выплаты воркеру (клиент принимает работу)
# ═══════════════════════════════════════════════════════════════════════════

class MedusaConfirmDealView(APIView):
    """
    POST /api/market/medusa/confirm-deal/<deal_id>/
    
    Клиент подтверждает выполнение → Tochka выплачивает воркеру.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, deal_id):
        try:
            deal = Deal.objects.select_for_update().get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Не найдена"}, status=404)

        if str(request.user.id) != str(deal.client_id):
            return Response(
                {"status": "error", "error": "Только заказчик"},
                status=403,
            )

        if deal.status != "delivered":
            return Response({
                "status": "error",
                "error": "Подтвердить можно только сданную работу",
            }, status=400)

        if not deal.medusa_order_ext_id or not deal.medusa_service_ext_id:
            return Response({
                "status": "error",
                "error": "Нет данных платёжной системы",
            }, status=400)

        try:
            medusa = MedusaService()
            medusa.make_decision(
                str(deal.medusa_order_ext_id),
                str(deal.medusa_service_ext_id),
                "confirmed",
            )
            # На stage — эмулируем выплату
            medusa.sandbox_full_cycle_after_decision(
                str(deal.medusa_order_ext_id),
                str(deal.medusa_service_ext_id),
                "confirmed",
            )

            deal.medusa_order_status = "completed"
            deal.save(update_fields=["medusa_order_status"])

            return Response({
                "status": "success",
                "message": "Деньги выплачиваются исполнителю",
            })

        except MedusaAPIError as e:
            logger.error("[Medusa] confirm-deal: HTTP %s — %s", e.status_code, e)
            return Response({
                "status": "error",
                "error": f"Ошибка банка: HTTP {e.status_code}. {str(e)[:200]}",
            }, status=502)


# ═══════════════════════════════════════════════════════════════════════════
# Отклонение сделки (возврат средств клиенту)
# ═══════════════════════════════════════════════════════════════════════════

class MedusaRejectDealView(APIView):
    """
    POST /api/market/medusa/reject-deal/<deal_id>/
    
    Отказ от сделки → Tochka возвращает деньги клиенту.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, deal_id):
        try:
            deal = Deal.objects.select_for_update().get(id=deal_id)
        except Deal.DoesNotExist:
            return Response({"status": "error", "error": "Не найдена"}, status=404)

        # Отклонить может и клиент, и воркер (при споре/возврате)
        if str(request.user.id) not in [str(deal.client_id), str(deal.worker_id)]:
            return Response({"status": "error", "error": "Нет доступа"}, status=403)

        if not deal.medusa_order_ext_id or not deal.medusa_service_ext_id:
            return Response({
                "status": "error",
                "error": "Нет данных платёжной системы",
            }, status=400)

        try:
            medusa = MedusaService()
            medusa.make_decision(
                str(deal.medusa_order_ext_id),
                str(deal.medusa_service_ext_id),
                "rejected",
            )
            medusa.sandbox_full_cycle_after_decision(
                str(deal.medusa_order_ext_id),
                str(deal.medusa_service_ext_id),
                "rejected",
            )

            deal.medusa_order_status = "cancelled"
            deal.save(update_fields=["medusa_order_status"])

            return Response({
                "status": "success",
                "message": "Деньги возвращаются заказчику",
            })

        except MedusaAPIError as e:
            logger.error("[Medusa] reject-deal: HTTP %s — %s", e.status_code, e)
            return Response({
                "status": "error",
                "error": f"Ошибка банка: HTTP {e.status_code}. {str(e)[:200]}",
            }, status=502)


# ═══════════════════════════════════════════════════════════════════════════
# Расчёт комиссий
# ═══════════════════════════════════════════════════════════════════════════

class MedusaCalculateCommissionView(APIView):
    """
    GET /api/market/medusa/calculate-commission/?price=1000
    
    Возвращает детализацию комиссий для указанной цены.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        price_str = request.query_params.get("price")
        if not price_str:
            return Response(
                {"status": "error", "error": "price обязателен"},
                status=400,
            )

        try:
            price = Decimal(str(price_str))
            if price <= 0:
                raise ValueError("price должен быть положительным")
        except (ValueError, Exception):
            return Response(
                {"status": "error", "error": "Некорректная цена"},
                status=400,
            )

        c = MedusaService.calculate_commission(price)

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
