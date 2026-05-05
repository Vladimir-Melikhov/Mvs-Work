"""
services/market/apps/services/medusa_service.py

Клиент Medusa API строго по документации Точка Банка.

POST — {"Data":{...}}, ответ {"Data":{...}}
GET  — без body, Accept: application/json
DELETE — пустой payload, пустые headers
"""

import os
import json
import uuid
import http.client
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

MEDUSA_COMMISSION_RATE = Decimal("0.80")
PLATFORM_COMMISSION_RATE = Decimal("0.50")
ACQUIRING_COMMISSION_RATE = Decimal("2.20")


class MedusaAPIError(Exception):
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class MedusaService:

    def __init__(self):
        self.is_stage = os.getenv("MEDUSA_ENV", "stage").lower() == "stage"
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
        self.frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")
        if not self.token:
            logger.error("[Medusa] TOCHKA_JWT_TOKEN not set!")

    # ─── HTTP ────────────────────────────────────────────────────────────────

    def _post(self, path, payload):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer " + self.token,
        }
        if self.sign_key_id:
            headers["Sign-Key-Id"] = self.sign_key_id
        if self.sign_body_value:
            headers["Sign-Body"] = self.sign_body_value
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        conn = http.client.HTTPSConnection(self.host, timeout=30)
        try:
            print("[Medusa] POST %s | %s" % (path, json.dumps(payload, ensure_ascii=False)[:2000]), flush=True)
            conn.request("POST", path, body, headers)
            res = conn.getresponse()
            raw = res.read().decode("utf-8", errors="replace")
            print("[Medusa] <- %s: %s" % (res.status, raw[:2000]), flush=True)
            if res.status not in (200, 201):
                raise MedusaAPIError("HTTP %s: %s" % (res.status, raw[:1500]), res.status, raw)
            return json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError as e:
            raise MedusaAPIError("Not JSON: %s" % e)
        except OSError as e:
            raise MedusaAPIError("Network: %s" % e)
        finally:
            conn.close()

    def _get(self, path):
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.token,
        }
        if self.sign_key_id:
            headers["Sign-Key-Id"] = self.sign_key_id
        if self.sign_body_value:
            headers["Sign-Body"] = self.sign_body_value
        conn = http.client.HTTPSConnection(self.host, timeout=30)
        try:
            logger.info("[Medusa] GET %s", path)
            conn.request("GET", path, "", headers)
            res = conn.getresponse()
            raw = res.read().decode("utf-8", errors="replace")
            logger.info("[Medusa] <- %s: %s", res.status, raw[:1500])
            if res.status not in (200, 201):
                raise MedusaAPIError("HTTP %s: %s" % (res.status, raw[:500]), res.status, raw)
            return json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError as e:
            raise MedusaAPIError("Not JSON: %s" % e)
        except OSError as e:
            raise MedusaAPIError("Network: %s" % e)
        finally:
            conn.close()

    def _delete(self, path):
        """DELETE — пробуем с полными заголовками, потом без."""
        conn = http.client.HTTPSConnection(self.host, timeout=30)
        try:
            # Сначала с авторизацией
            headers = {
                "Accept": "application/json",
                "Authorization": "Bearer " + self.token,
            }
            if self.sign_key_id:
                headers["Sign-Key-Id"] = self.sign_key_id
            if self.sign_body_value:
                headers["Sign-Body"] = self.sign_body_value

            logger.info("[Medusa] DELETE %s (with auth)", path)
            conn.request("DELETE", path, "", headers)
            res = conn.getresponse()
            raw = res.read().decode("utf-8", errors="replace")
            logger.info("[Medusa] <- DELETE %s: %s", res.status, raw[:500])
            return res.status in (200, 201, 204)
        except Exception as e:
            logger.error("[Medusa] DELETE error: %s", e)
            return False
        finally:
            conn.close()

    # ─── Комиссии ────────────────────────────────────────────────────────────

    @staticmethod
    def calculate_commission(service_price):
        price = Decimal(str(service_price))
        q = Decimal("0.01")
        platform = (price * PLATFORM_COMMISSION_RATE / 100).quantize(q, ROUND_HALF_UP)
        medusa = (price * MEDUSA_COMMISSION_RATE / 100).quantize(q, ROUND_HALF_UP)
        acquiring = ((price + platform + medusa) * ACQUIRING_COMMISSION_RATE / 100).quantize(q, ROUND_HALF_UP)
        total_commission = platform + medusa + acquiring
        return {
            "service_price": price,
            "platform_commission": platform,
            "medusa_commission": medusa,
            "acquiring_commission": acquiring,
            "total_commission": total_commission,
            "total_amount": price + total_commission,
        }

    # ─── Recipients v1.0 ─────────────────────────────────────────────────────

    def create_recipient(self, ext_id, name):
        payload = {"Data": {"extId": str(ext_id), "name": (name or "Worker")[:128]}}
        resp = self._post(self.base_v1 + "/recipients", payload)
        return resp.get("Data", {})

    def get_recipient(self, ext_id):
        resp = self._get(self.base_v1 + "/recipients/" + str(ext_id))
        return resp.get("Data", {})

    def add_card_payout_method(self, recipient_ext_id, redirect_url, payout_method_ext_id=None):
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
        resp = self._post(
            self.base_v1 + "/recipients/" + str(recipient_ext_id) + "/payout_methods/cards",
            payload,
        )
        form_url = resp.get("Data", {}).get("formUrl", "")
        return {"formUrl": form_url, "payoutMethodExtId": payout_method_ext_id}

    def delete_card_payout_method(self, recipient_ext_id, payout_method_ext_id):
        path = self.base_v1 + "/recipients/" + str(recipient_ext_id) + "/payout_methods/cards/" + str(payout_method_ext_id)
        ok = self._delete(path)
        if ok:
            logger.info("[Medusa] Card deleted: %s", payout_method_ext_id)
        else:
            logger.error("[Medusa] Card NOT deleted: %s", payout_method_ext_id)
        return ok

    # ─── Orders V2 ────────────────────────────────────────────────────────────

    def create_order(self, order_ext_id, service_price, recipient_ext_id, card_ext_id,
                     customer_email, redirect_url, redirect_fail_url,
                     purpose="Оплата заказа на MVS-Work", payment_url_ttl=60, consumer_id=None):
        commission = self.calculate_commission(service_price)
        service_ext_id = str(uuid.uuid4())
        incoming = {
            "type": "acquiring",
            "redirectUrl": redirect_url,
            "redirectFailUrl": redirect_fail_url,
            "paymentUrlTtl": int(payment_url_ttl),
            "purpose": (purpose or "Оплата")[:256],
        }
        if consumer_id:
            incoming["consumerId"] = str(consumer_id)

        payload = {
            "Data": {
                "orderExtId": str(order_ext_id),
                "IncomingPayment": incoming,
                "Services": [{
                    "extId": service_ext_id,
                    "price": str(commission["service_price"]),
                    "commission": str(commission["total_commission"]),
                    "Recipient": {
                        "extId": str(recipient_ext_id),
                        "method": "CARD",
                        "cardExtId": str(card_ext_id),
                    },
                    "startDecision": "not_decided",
                }],
                "Receipt": {
                    "email": customer_email or "customer@mvs-work.ru",
                    "name": (purpose or "Услуга")[:128],
                    "vatType": os.getenv("MEDUSA_VAT_TYPE", "none"),
                    "paymentMethod": "full_payment",
                    "paymentObject": "service",
                },
            }
        }

        resp = self._post(self.base_v2 + "/orders", payload)
        data = resp.get("Data", {})
        payment_url = data.get("paymentUrl") or resp.get("paymentUrl") or ""
        return {
            "orderExtId": str(order_ext_id),
            "serviceExtId": service_ext_id,
            "paymentUrl": payment_url,
            "total_amount": commission["total_amount"],
            "commission_details": commission,
        }

    def get_order(self, order_ext_id):
        resp = self._get(self.base_v1 + "/orders/" + str(order_ext_id))
        return resp.get("Data", resp)

    def make_decision(self, order_ext_id, service_ext_id, decision):
        if decision not in ("confirmed", "rejected"):
            raise ValueError("decision: confirmed or rejected")
        payload = {"Data": {"Decisions": [{"serviceExtId": str(service_ext_id), "decision": decision}]}}
        return self._post(self.base_v1 + "/orders/" + str(order_ext_id) + "/decisions", payload)

    # ─── Sandbox ──────────────────────────────────────────────────────────────

    def _sandbox(self, endpoint, payload):
        if not self.is_stage:
            return {}
        try:
            return self._post(self.base_v1 + "/sandbox/" + endpoint, payload)
        except MedusaAPIError as e:
            logger.warning("[Sandbox] %s: %s", endpoint, e)
            return {}

    def sandbox_mark_order_paid(self, order_ext_id):
        return self._sandbox("mark_order_paid_by_acquirer", {"orderExtId": str(order_ext_id)})

    def sandbox_proceed_payout(self, service_ext_id):
        return self._sandbox("proceed_service_payout_to_recipient", {"serviceExtId": str(service_ext_id)})

    def sandbox_proceed_refund(self, service_ext_id):
        return self._sandbox("proceed_refund", {"serviceExtId": str(service_ext_id)})

    def sandbox_full_cycle_after_decision(self, order_ext_id, service_ext_id, decision):
        if not self.is_stage:
            return
        if decision == "confirmed":
            self.sandbox_proceed_payout(service_ext_id)
            self._sandbox("proceed_service_payout_commission", {"serviceExtId": service_ext_id})
            self._sandbox("proceed_acquiring_commission", {"orderExtId": order_ext_id})
            self._sandbox("move_platform_commission_to_commission_account", {"orderExtId": order_ext_id})
            self._sandbox("proceed_platform_commission", {"orderExtId": order_ext_id})
        elif decision == "rejected":
            self.sandbox_proceed_refund(service_ext_id)
            self._sandbox("proceed_acquiring_commission", {"orderExtId": order_ext_id})
