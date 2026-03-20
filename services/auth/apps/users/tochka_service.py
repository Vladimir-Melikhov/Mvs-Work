# services/auth/apps/users/tochka_service.py
import os
import json
import http.client
import logging
from decimal import Decimal
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

TOCHKA_HOST = "enter.tochka.com"
TOCHKA_BASE_PATH = "/uapi/acquiring/v1.0"

SUBSCRIPTION_PRICE = Decimal("444.00")
SUBSCRIPTION_TITLE = "Подписка MVS-Work (1 месяц)"


class TochkaAPIError(Exception):
    pass


class TochkaPaymentService:

    def __init__(self):
        self.token = os.getenv("TOCHKA_JWT_TOKEN", "")
        # customerCode ИП/юрлица — из .env
        self.customer_code = os.getenv("TOCHKA_CUSTOMER_CODE", "")
        self.merchant_id = os.getenv("TOCHKA_MERCHANT_ID", "")
        self.frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")

        if not self.token:
            logger.warning("[Tochka] TOCHKA_JWT_TOKEN не задан в .env")
        if not self.customer_code:
            logger.warning("[Tochka] TOCHKA_CUSTOMER_CODE не задан в .env")
        else:
            logger.info("[Tochka] customerCode: %s", self.customer_code)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def _make_request(self, method: str, path: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
        conn = http.client.HTTPSConnection(TOCHKA_HOST, timeout=15)
        body = json.dumps(payload) if payload else ""

        try:
            conn.request(method, path, body, self._get_headers())
            res = conn.getresponse()
            raw = res.read().decode("utf-8")
            logger.debug("[Tochka] %s %s → %s: %s", method, path, res.status, raw[:500])

            if res.status not in (200, 201):
                logger.error("[Tochka] HTTP %s: %s", res.status, raw[:500])
                raise TochkaAPIError(f"Точка API вернул HTTP {res.status}: {raw[:300]}")

            return json.loads(raw)

        except json.JSONDecodeError as e:
            raise TochkaAPIError(f"Ошибка парсинга ответа Точки: {e}")
        except OSError as e:
            raise TochkaAPIError(f"Сетевая ошибка при запросе к Точке: {e}")
        finally:
            conn.close()

    def create_subscription(self, user_id: str, user_email: str, payment_link_id: str) -> Dict[str, Any]:
        if not self.customer_code:
            raise TochkaAPIError("TOCHKA_CUSTOMER_CODE не задан в .env")

        payload = {
            "Data": {
                "customerCode": self.customer_code,
                "amount": str(SUBSCRIPTION_PRICE),
                "purpose": SUBSCRIPTION_TITLE,
                "redirectUrl": f"{self.frontend_url}/profile?subscription=success",
                "failRedirectUrl": f"{self.frontend_url}/profile?subscription=fail",
                "saveCard": True,
                "paymentLinkId": payment_link_id,
                "Options": {
                    "trancheCount": 120,
                    "period": "Month",
                },
                "Client": {
                    "Email": user_email,
                },
                "Items": [
                    {
                        "name": SUBSCRIPTION_TITLE,
                        "amount": str(SUBSCRIPTION_PRICE),
                        "quantity": 1,
                        "vatType": os.getenv("TOCHKA_VAT_TYPE", "none"),
                        "paymentMethod": "full_payment",
                        "paymentObject": "service",
                    }
                ],
            }
        }

        if self.merchant_id:
            payload["Data"]["merchantId"] = self.merchant_id

        logger.info(
            "[Tochka] Создаём подписку. customerCode=%s email=%s paymentLinkId=%s",
            self.customer_code, user_email, payment_link_id
        )

        response = self._make_request("POST", f"{TOCHKA_BASE_PATH}/subscriptions", payload)

        data = response.get("Data", {})
        payment_link = data.get("paymentLink")
        operation_id = data.get("operationId")
        consumer_id = data.get("consumerId", "")

        if not payment_link or not operation_id:
            raise TochkaAPIError(f"Точка не вернула paymentLink или operationId. Ответ: {data}")

        logger.info("[Tochka] ✅ Подписка создана. operationId=%s", operation_id)

        return {
            "payment_link": payment_link,
            "operation_id": operation_id,
            "consumer_id": consumer_id,
        }

    def get_subscription_status(self, operation_id: str) -> str:
        path = f"{TOCHKA_BASE_PATH}/subscriptions/{operation_id}/status"
        response = self._make_request("GET", path)
        tochka_status = response.get("Data", {}).get("status", "Unknown")
        logger.info("[Tochka] Статус %s: %s", operation_id, tochka_status)
        return tochka_status
