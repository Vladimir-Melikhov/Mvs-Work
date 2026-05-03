"""
services/market/apps/services/medusa_service.py

Клиент API Безопасных сделок Точка Банка (Medusa).

Документация: https://developers.tochka.com/docs/medusa/

STAGE: stage-uapi.tochka.com
PROD:  enter.tochka.com

Авторизация на STAGE:
  Authorization: Bearer sandbox.jwt.token
  Sign-Key-Id: 7715014b-3d11-4c8a-add9-8cbc81364cea
  Sign-Body: 12345

На STAGE Sign-Body=12345 обязателен для ВСЕХ методов (включая GET и DELETE).
Без него возвращается 403 "The access token is missing".
"""

import os
import json
import uuid
import http.client
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Комиссии (%)
MEDUSA_COMMISSION_RATE = Decimal("0.80")     # Комиссия Tochka Medusa (фиксированная)
PLATFORM_COMMISSION_RATE = Decimal("0.50")   # Наша комиссия
ACQUIRING_COMMISSION_RATE = Decimal("2.20")  # Эквайринг


class MedusaAPIError(Exception):
    """Ошибка API Medusa"""
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class MedusaService:
    """Клиент Medusa API"""

    def __init__(self):
        self.is_stage = os.getenv("MEDUSA_ENV", "stage").lower() == "stage"

        # JWT-токен
        # На stage это "sandbox.jwt.token"
        # На prod — реальный JWT с правами medusa_*
        self.token = os.getenv("MEDUSA_JWT_TOKEN") or os.getenv("TOCHKA_JWT_TOKEN", "")

        if self.is_stage:
            self.host = "stage-uapi.tochka.com"
            self.sign_key_id = os.getenv("MEDUSA_SIGN_KEY_ID", "7715014b-3d11-4c8a-add9-8cbc81364cea")
            self.sign_body_value = os.getenv("MEDUSA_SIGN_BODY", "12345")
        else:
            self.host = "enter.tochka.com"
            self.sign_key_id = os.getenv("MEDUSA_SIGN_KEY_ID", "")
            self.sign_body_value = os.getenv("MEDUSA_SIGN_BODY", "")

        self.base_v1 = "/uapi/medusa/v1.0"
        self.base_v2 = "/uapi/medusa/v2.0"
        self.base_v3 = "/uapi/medusa/v3.0"
        self.frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")

        if not self.token:
            logger.error("[Medusa] ❌ TOCHKA_JWT_TOKEN / MEDUSA_JWT_TOKEN не задан!")

    # ─── HTTP ────────────────────────────────────────────────────────────────

    def _headers(self, method: str) -> Dict[str, str]:
        """Заголовки запроса."""
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        if self.sign_key_id:
            h["Sign-Key-Id"] = self.sign_key_id

        # На STAGE Медуза требует Sign-Body=12345 для ВСЕХ методов.
        # Без него — 403 "The access token is missing".
        if self.sign_body_value:
            h["Sign-Body"] = self.sign_body_value

        return h

    def _request(self, method: str, path: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
        """Отправить HTTP-запрос к Medusa API"""
        body = json.dumps(payload, ensure_ascii=False) if payload else ""
        body_bytes = body.encode("utf-8") if body else b""
        conn = http.client.HTTPSConnection(self.host, timeout=30)
        headers = self._headers(method)

        try:
            logger.info("[Medusa] → %s %s", method, path)
            if payload:
                # Полный payload в логах (полезно при отладке на stage)
                logger.info("[Medusa] payload: %s", json.dumps(payload, ensure_ascii=False)[:2000])

            conn.request(method, path, body_bytes, headers)
            res = conn.getresponse()
            raw = res.read().decode("utf-8", errors="replace")

            logger.info("[Medusa] ← HTTP %s: %s", res.status, raw[:2000])

            if res.status not in (200, 201, 204):
                raise MedusaAPIError(
                    f"HTTP {res.status}: {raw[:500]}",
                    status_code=res.status,
                    response_body=raw,
                )

            return json.loads(raw) if raw.strip() else {}

        except json.JSONDecodeError as e:
            raise MedusaAPIError(f"Не JSON-ответ: {e}")
        except OSError as e:
            raise MedusaAPIError(f"Сетевая ошибка: {e}")
        finally:
            conn.close()

    # ─── Комиссии ────────────────────────────────────────────────────────────

    @staticmethod
    def calculate_commission(service_price: Decimal) -> Dict[str, Decimal]:
        """
        Рассчитать все комиссии для цены услуги.

        Формула по доке Точки:
          1. platform  = price × 0.5%
          2. medusa    = price × 0.8%
          3. acquiring = (price + platform + medusa) × 2.2%
          4. commission (в поле Services[].commission) = platform + medusa + acquiring
          5. total_amount (что платит клиент) = price + commission

        Пример для price=10000:
          platform   = 50.00
          medusa     = 80.00
          acquiring  = (10000 + 50 + 80) × 0.022 = 222.86
          commission = 352.86
          total_amount = 10352.86
        """
        price = Decimal(str(service_price))
        q = Decimal("0.01")

        platform = (price * PLATFORM_COMMISSION_RATE / 100).quantize(q, ROUND_HALF_UP)
        medusa = (price * MEDUSA_COMMISSION_RATE / 100).quantize(q, ROUND_HALF_UP)
        transaction_sum = price + platform + medusa
        acquiring = (transaction_sum * ACQUIRING_COMMISSION_RATE / 100).quantize(q, ROUND_HALF_UP)
        total_commission = platform + medusa + acquiring
        total_amount = price + total_commission

        return {
            "service_price": price,
            "platform_commission": platform,
            "medusa_commission": medusa,
            "acquiring_commission": acquiring,
            "total_commission": total_commission,
            "total_amount": total_amount,
        }

    # ─── Recipients (Получатели) v1.0 ────────────────────────────────────────

    def create_recipient(self, ext_id: str, name: str) -> Dict[str, Any]:
        """Создать получателя. extId — UUID воркера в нашей системе."""
        payload = {
            "Data": {
                "extId": str(ext_id),
                "name": (name or "Worker")[:128],
            }
        }
        resp = self._request("POST", f"{self.base_v1}/recipients", payload)
        logger.info("[Medusa] ✅ Recipient создан: %s", ext_id)
        return resp.get("Data", {})

    def get_recipient(self, ext_id: str) -> Dict[str, Any]:
        """Получить данные получателя, включая список привязанных карт."""
        resp = self._request("GET", f"{self.base_v1}/recipients/{ext_id}")
        return resp.get("Data", {})

    def add_card_payout_method(
        self,
        recipient_ext_id: str,
        redirect_url: str,
        payout_method_ext_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Получить ссылку на форму токенизации карты.

        Возвращает:
          formUrl — ссылка, куда редиректить пользователя для ввода данных карты
          payoutMethodExtId — UUID, который мы задали этой карте
        """
        if not payout_method_ext_id:
            payout_method_ext_id = str(uuid.uuid4())

        payload = {
            "Data": {
                "CardPayoutMethod": {
                    "redirectUrl": redirect_url,
                    "payoutMethodExtId": payout_method_ext_id,
                }
            }
        }

        resp = self._request(
            "POST",
            f"{self.base_v1}/recipients/{recipient_ext_id}/payout_methods/cards",
            payload,
        )

        data = resp.get("Data", {})
        form_url = data.get("formUrl", "")

        logger.info(
            "[Medusa] ✅ Форма карты: %s... (payoutMethodExtId=%s)",
            form_url[:60], payout_method_ext_id,
        )

        return {
            "formUrl": form_url,
            "payoutMethodExtId": payout_method_ext_id,
        }

    def delete_card_payout_method(
        self,
        recipient_ext_id: str,
        payout_method_ext_id: str,
    ) -> bool:
        """Удалить карту"""
        try:
            self._request(
                "DELETE",
                f"{self.base_v1}/recipients/{recipient_ext_id}/payout_methods/cards/{payout_method_ext_id}",
            )
            logger.info("[Medusa] ✅ Карта удалена: %s", payout_method_ext_id)
            return True
        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка удаления карты: %s", e)
            return False

    # ─── Orders v3.0 ──────────────────────────────────────────────────────────

    def create_order(
        self,
        order_ext_id: str,
        service_price: Decimal,
        recipient_ext_id: str,
        card_ext_id: str,
        customer_email: str,
        redirect_url: str,
        redirect_fail_url: str,
        purpose: str = "Оплата заказа на MVS-Work",
        payment_url_ttl: int = 60,
        consumer_id: Optional[str] = None,
        with_receipt: bool = True,
    ) -> Dict[str, Any]:
        """
        Создать заказ (безопасную сделку) по v3 API.

        Структура соответствует документации v3:
        https://developers.tochka.com/docs/medusa/api/create-new-order-medusa-v-3-0-orders-post

        Если API возвращает 424 "orderCantBeCreated" — это обычно означает что
        на стороне Точки твой аккаунт не имеет права создавать ордера.
        Это НЕ ошибка структуры payload. Решается через саппорт Точки.
        """
        commission = self.calculate_commission(service_price)
        service_ext_id = str(uuid.uuid4())

        details: Dict[str, Any] = {
            "sbpNeeded": False,
            "cardNeeded": True,
            "redirectUrl": redirect_url,
            "failRedirectUrl": redirect_fail_url,
            "ttl": int(payment_url_ttl),
            "purpose": (purpose or "Оплата заказа")[:256],
        }
        if consumer_id:
            details["consumerId"] = str(consumer_id)

        payload: Dict[str, Any] = {
            "Data": {
                "extId": str(order_ext_id),
                "IncomingPayment": {
                    "type": "acquiring",
                    "Details": details,
                },
                "Services": [
                    {
                        "extId": service_ext_id,
                        "price": str(commission["service_price"]),
                        "commission": str(commission["total_commission"]),
                        "Recipient": {
                            "extId": str(recipient_ext_id),
                            "payoutExtId": str(card_ext_id),
                        },
                        "startDecision": "not_decided",
                    }
                ],
            }
        }

        # Receipt — по доке опциональный объект.
        # Нужен для фискализации (отправки чека в ОФД).
        if with_receipt:
            payload["Data"]["Receipt"] = {
                "email": customer_email or "customer@mvs-work.ru",
                "name": (purpose or "Услуга")[:128],
                "vatType": os.getenv("MEDUSA_VAT_TYPE", "none"),
                "paymentMethod": "full_payment",
                "paymentObject": "service",
            }

        resp = self._request("POST", f"{self.base_v3}/orders", payload)
        data = resp.get("Data", {})

        logger.info(
            "[Medusa] ✅ Order создан: %s (сумма %s₽, комиссия %s₽, paymentUrl: %s...)",
            order_ext_id,
            commission["total_amount"],
            commission["total_commission"],
            str(data.get("paymentUrl", ""))[:60],
        )

        return {
            "orderExtId": str(order_ext_id),
            "serviceExtId": service_ext_id,
            "paymentUrl": data.get("paymentUrl", ""),
            "total_amount": commission["total_amount"],
            "commission_details": commission,
        }

    def get_order(self, order_ext_id: str) -> Dict[str, Any]:
        """Получить данные заказа."""
        resp = self._request("GET", f"{self.base_v1}/orders/{order_ext_id}")
        return resp.get("Data", {})

    def make_decision(
        self,
        order_ext_id: str,
        service_ext_id: str,
        decision: str,
    ) -> Dict[str, Any]:
        """
        Принятие решения заказчиком:
          confirmed — подтверждаем выполнение (выплата воркеру)
          rejected  — отказ (возврат заказчику)
        """
        if decision not in ("confirmed", "rejected"):
            raise ValueError("decision должен быть 'confirmed' или 'rejected'")

        payload = {
            "Data": {
                "Decisions": [
                    {
                        "serviceExtId": str(service_ext_id),
                        "decision": decision,
                    }
                ]
            }
        }

        resp = self._request(
            "POST",
            f"{self.base_v1}/orders/{order_ext_id}/decisions",
            payload,
        )

        logger.info(
            "[Medusa] %s заказ %s",
            "✅ Подтверждён" if decision == "confirmed" else "❌ Отклонён",
            order_ext_id,
        )
        return resp.get("Data", {})

    # ─── Sandbox (только STAGE) ───────────────────────────────────────────────

    def _sandbox(self, path: str, payload: Dict) -> Dict[str, Any]:
        """Внутренний метод для sandbox-запросов"""
        return self._request("POST", f"{self.base_v1}{path}", {"Data": payload})

    def sandbox_mark_order_paid(self, order_ext_id: str) -> Dict[str, Any]:
        """Эмулирует успешную оплату заказа пользователем"""
        if not self.is_stage:
            return {}
        try:
            return self._sandbox(
                "/sandbox/mark_order_paid_by_acquirer",
                {"orderExtId": str(order_ext_id)},
            )
        except MedusaAPIError as e:
            logger.warning("[Sandbox] mark_paid: %s", e)
            return {}

    def sandbox_proceed_payout(self, service_ext_id: str) -> Dict[str, Any]:
        """Эмулирует выплату воркеру"""
        if not self.is_stage:
            return {}
        try:
            return self._sandbox(
                "/sandbox/proceed_service_payout_to_recipient",
                {"serviceExtId": str(service_ext_id)},
            )
        except MedusaAPIError as e:
            logger.warning("[Sandbox] proceed_payout: %s", e)
            return {}

    def sandbox_proceed_refund(self, service_ext_id: str) -> Dict[str, Any]:
        """Эмулирует возврат заказчику"""
        if not self.is_stage:
            return {}
        try:
            return self._sandbox(
                "/sandbox/proceed_refund",
                {"serviceExtId": str(service_ext_id)},
            )
        except MedusaAPIError as e:
            logger.warning("[Sandbox] proceed_refund: %s", e)
            return {}

    def sandbox_full_cycle_after_decision(
        self,
        order_ext_id: str,
        service_ext_id: str,
        decision: str,
    ) -> None:
        """Полный цикл после принятия решения (только stage)"""
        if not self.is_stage:
            return
        if decision == "confirmed":
            self.sandbox_proceed_payout(service_ext_id)
        elif decision == "rejected":
            self.sandbox_proceed_refund(service_ext_id)