# services/market/apps/services/medusa_service.py
"""
Клиент API Безопасных сделок Точка Банка (Medusa).

Все запросы обёрнуты в { "Data": { ... } } — как требует API.
Create Order использует v3.0: /uapi/medusa/v3.0/orders.
Остальные методы — v1.0: /uapi/medusa/v1.0/...

Окружения:
  STAGE: stage-uapi.tochka.com
  PROD:  enter.tochka.com
"""

import os
import json
import uuid
import http.client
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ── Константы комиссий ────────────────────────────────────────────────────────
MEDUSA_COMMISSION_RATE = Decimal("0.80")    # Комиссия Точки
PLATFORM_COMMISSION_RATE = Decimal("0.50")  # Комиссия MVS-Work
ACQUIRING_COMMISSION_RATE = Decimal("2.20") # Комиссия эквайринга


class MedusaAPIError(Exception):
    """Ошибка при работе с Medusa API"""
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class MedusaService:
    """
    Клиент для работы с API Безопасных сделок Точка Банка.
    """

    def __init__(self):
        self.is_stage = os.getenv("MEDUSA_ENV", "stage").lower() == "stage"

        # JWT-токен — тот же что для эквайринга (TOCHKA_JWT_TOKEN).
        # Можно переопределить через MEDUSA_JWT_TOKEN если будет отдельный.
        self.token = os.getenv("MEDUSA_JWT_TOKEN") or os.getenv("TOCHKA_JWT_TOKEN", "")

        if self.is_stage:
            self.host = "stage-uapi.tochka.com"
            self.sign_key_id = os.getenv("MEDUSA_SIGN_KEY_ID", "7715014b-3d11-4c8a-add9-8cbc81364cea")
            self.sign_body = os.getenv("MEDUSA_SIGN_BODY", "12345")
        else:
            self.host = "enter.tochka.com"
            self.sign_key_id = os.getenv("MEDUSA_SIGN_KEY_ID", "")
            self.sign_body = os.getenv("MEDUSA_SIGN_BODY", "")

        self.base_path_v1 = "/uapi/medusa/v1.0"
        self.base_path_v3 = "/uapi/medusa/v3.0"
        self.frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")

        if not self.token:
            logger.warning("[Medusa] TOCHKA_JWT_TOKEN не задан — запросы вернут 403")
        if not self.sign_key_id:
            logger.warning("[Medusa] MEDUSA_SIGN_KEY_ID не задан")

    # ── HTTP-слой ─────────────────────────────────────────────────────────────

    def _get_headers(self, method: str = "POST") -> Dict[str, str]:
        """
        Заголовки запроса.
        Authorization: Bearer <jwt> — обязателен для всех запросов.
        Sign-Key-Id / Sign-Body    — для stage-окружения.
        Sign-Body пустой для GET, "12345" для остальных методов на stage.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Sign-Key-Id": self.sign_key_id,
        }

        if method.upper() == "GET":
            headers["Sign-Body"] = ""
        else:
            headers["Sign-Body"] = self.sign_body

        return headers

    def _make_request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Выполнить HTTP-запрос к API Медузы."""
        body = json.dumps(payload) if payload else ""
        conn = http.client.HTTPSConnection(self.host, timeout=30)
        headers = self._get_headers(method)

        try:
            conn.request(method, path, body, headers)
            res = conn.getresponse()
            raw = res.read().decode("utf-8")

            logger.info(
                "[Medusa] %s %s → HTTP %s | Body: %s",
                method, path, res.status, raw[:500]
            )

            if res.status not in (200, 201):
                logger.error("[Medusa] HTTP %s: %s", res.status, raw[:500])
                raise MedusaAPIError(
                    f"Medusa API вернул HTTP {res.status}: {raw[:300]}",
                    status_code=res.status,
                    response_body=raw,
                )

            return json.loads(raw) if raw.strip() else {}

        except json.JSONDecodeError as e:
            raise MedusaAPIError(f"Ошибка парсинга ответа Medusa: {e}")
        except OSError as e:
            raise MedusaAPIError(f"Сетевая ошибка при запросе к Medusa: {e}")
        finally:
            conn.close()

    # ── Расчёт комиссий ───────────────────────────────────────────────────────

    @staticmethod
    def calculate_commission(service_price: Decimal) -> Dict[str, Decimal]:
        price = Decimal(str(service_price))

        platform_commission = (price * PLATFORM_COMMISSION_RATE / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        medusa_commission = (price * MEDUSA_COMMISSION_RATE / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        transaction_sum = price + platform_commission + medusa_commission
        acquiring_commission = (transaction_sum * ACQUIRING_COMMISSION_RATE / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_commission = platform_commission + medusa_commission + acquiring_commission
        total_amount = price + total_commission

        return {
            "platform_commission": platform_commission,
            "medusa_commission": medusa_commission,
            "acquiring_commission": acquiring_commission,
            "total_commission": total_commission,
            "total_amount": total_amount,
            "service_price": price,
        }

    # ── 1. Получатели (Recipients) v1.0 ──────────────────────────────────────

    def create_recipient(self, recipient_ext_id: str, name: str) -> Dict[str, Any]:
        payload = {
            "Data": {
                "extId": str(recipient_ext_id),
                "name": name[:128],
            }
        }
        response = self._make_request("POST", f"{self.base_path_v1}/recipients", payload)
        data = response.get("Data", {})
        logger.info("[Medusa] ✅ Получатель создан: %s (%s)", recipient_ext_id, name)
        return data

    def get_recipient(self, recipient_ext_id: str) -> Dict[str, Any]:
        response = self._make_request("GET", f"{self.base_path_v1}/recipients/{recipient_ext_id}")
        return response.get("Data", {})

    def add_card_payout_method(
        self,
        recipient_ext_id: str,
        redirect_url: str,
        payout_method_ext_id: Optional[str] = None,
    ) -> Dict[str, Any]:
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

        response = self._make_request(
            "POST",
            f"{self.base_path_v1}/recipients/{recipient_ext_id}/payout_methods/cards",
            payload,
        )

        data = response.get("Data", {})
        form_url = data.get("formUrl", "")

        logger.info(
            "[Medusa] ✅ Форма добавления карты: %s (получатель=%s)",
            form_url[:80], recipient_ext_id,
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
        try:
            self._make_request(
                "DELETE",
                f"{self.base_path_v1}/recipients/{recipient_ext_id}/payout_methods/cards/{payout_method_ext_id}",
            )
            logger.info("[Medusa] ✅ Карта удалена: %s", payout_method_ext_id)
            return True
        except MedusaAPIError as e:
            logger.error("[Medusa] Ошибка удаления карты: %s", e)
            return False

    # ── 2. Заказы v3.0 ────────────────────────────────────────────────────────

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
    ) -> Dict[str, Any]:
        commission = self.calculate_commission(service_price)
        service_ext_id = str(uuid.uuid4())

        details = {
            "sbpNeeded": False,
            "cardNeeded": True,
            "redirectUrl": redirect_url,
            "failRedirectUrl": redirect_fail_url,
            "ttl": payment_url_ttl,
            "purpose": purpose[:256],
        }

        if consumer_id:
            details["consumerId"] = str(consumer_id)

        payload = {
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
                "Receipt": {
                    "email": customer_email,
                    "name": purpose[:128],
                    "vatType": os.getenv("MEDUSA_VAT_TYPE", "none"),
                    "paymentMethod": "full_payment",
                    "paymentObject": "service",
                },
            }
        }

        response = self._make_request("POST", f"{self.base_path_v3}/orders", payload)
        data = response.get("Data", {})
        payment_url = data.get("paymentUrl", "")

        logger.info(
            "[Medusa] ✅ Заказ создан: %s | Сумма: %s₽ | Комиссия: %s₽",
            order_ext_id, commission["total_amount"], commission["total_commission"],
        )

        return {
            "orderExtId": str(order_ext_id),
            "serviceExtId": service_ext_id,
            "paymentUrl": payment_url,
            "total_amount": commission["total_amount"],
            "commission_details": commission,
        }

    def get_order(self, order_ext_id: str) -> Dict[str, Any]:
        response = self._make_request("GET", f"{self.base_path_v1}/orders/{order_ext_id}")
        return response.get("Data", {})

    def get_order_list(self, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        response = self._make_request(
            "GET",
            f"{self.base_path_v1}/orders?offset={offset}&limit={limit}",
        )
        return response.get("Data", {})

    def make_decision(
        self,
        order_ext_id: str,
        service_ext_id: str,
        decision: str,
    ) -> Dict[str, Any]:
        if decision not in ("confirmed", "rejected"):
            raise ValueError(f"decision должен быть 'confirmed' или 'rejected', получено: {decision}")

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

        response = self._make_request(
            "POST",
            f"{self.base_path_v1}/orders/{order_ext_id}/decisions",
            payload,
        )

        action = "подтверждён ✅" if decision == "confirmed" else "отклонён ❌"
        logger.info("[Medusa] Заказ %s — %s", order_ext_id, action)

        return response.get("Data", {})

    # ── 3. Sandbox-методы (только STAGE) ──────────────────────────────────────

    def _sandbox_request(self, path: str, payload: Dict) -> Dict[str, Any]:
        return self._make_request("POST", f"{self.base_path_v1}{path}", {"Data": payload})

    def sandbox_mark_order_paid(self, order_ext_id: str) -> Dict[str, Any]:
        if not self.is_stage:
            logger.warning("[Medusa] sandbox вызван в PROD, пропускаем")
            return {}
        return self._sandbox_request(
            "/sandbox/mark_order_paid_by_acquirer",
            {"orderExtId": str(order_ext_id)},
        )

    def sandbox_mark_order_payment_failed(self, order_ext_id: str) -> Dict[str, Any]:
        if not self.is_stage:
            return {}
        return self._sandbox_request(
            "/sandbox/mark_order_acquiring_payment_failed",
            {"orderExtId": str(order_ext_id)},
        )

    def sandbox_proceed_payout(self, service_ext_id: str) -> Dict[str, Any]:
        if not self.is_stage:
            return {}
        return self._sandbox_request(
            "/sandbox/proceed_service_payout_to_recipient",
            {"serviceExtId": str(service_ext_id)},
        )

    def sandbox_proceed_refund(self, service_ext_id: str) -> Dict[str, Any]:
        if not self.is_stage:
            return {}
        return self._sandbox_request(
            "/sandbox/proceed_refund",
            {"serviceExtId": str(service_ext_id)},
        )

    def sandbox_proceed_payout_commission(self, service_ext_id: str) -> Dict[str, Any]:
        if not self.is_stage:
            return {}
        return self._sandbox_request(
            "/sandbox/proceed_service_payout_commission",
            {"serviceExtId": str(service_ext_id)},
        )

    def sandbox_proceed_acquiring_commission(self, order_ext_id: str) -> Dict[str, Any]:
        if not self.is_stage:
            return {}
        return self._sandbox_request(
            "/sandbox/proceed_acquiring_commission",
            {"orderExtId": str(order_ext_id)},
        )

    def sandbox_move_platform_commission(self, order_ext_id: str) -> Dict[str, Any]:
        if not self.is_stage:
            return {}
        return self._sandbox_request(
            "/sandbox/move_platform_commission_to_commission_account",
            {"orderExtId": str(order_ext_id)},
        )

    def sandbox_proceed_platform_commission(self, order_ext_id: str) -> Dict[str, Any]:
        if not self.is_stage:
            return {}
        return self._sandbox_request(
            "/sandbox/proceed_platform_commission",
            {"orderExtId": str(order_ext_id)},
        )

    def sandbox_full_cycle_after_decision(
        self,
        order_ext_id: str,
        service_ext_id: str,
        decision: str,
    ) -> None:
        if not self.is_stage:
            return

        try:
            if decision == "confirmed":
                self.sandbox_proceed_payout(service_ext_id)
                self.sandbox_proceed_payout_commission(service_ext_id)
                self.sandbox_proceed_acquiring_commission(order_ext_id)
                self.sandbox_move_platform_commission(order_ext_id)
                self.sandbox_proceed_platform_commission(order_ext_id)
                logger.info("[Medusa/Sandbox] ✅ Полный цикл выплаты завершён")

            elif decision == "rejected":
                self.sandbox_proceed_refund(service_ext_id)
                self.sandbox_proceed_acquiring_commission(order_ext_id)
                logger.info("[Medusa/Sandbox] ✅ Возврат завершён")

        except MedusaAPIError as e:
            logger.warning("[Medusa/Sandbox] ⚠️ Ошибка шага: %s", e)
