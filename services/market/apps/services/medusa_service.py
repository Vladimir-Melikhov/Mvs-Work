# services/market/apps/services/medusa_service.py
"""
Клиент API Безопасных сделок Точка Банка (Medusa).

Полный цикл:
  1. Create Recipient — регистрация исполнителя
  2. Add Card Payout Method — привязка карты исполнителя (токенизация)
  3. Get Recipient — проверка карт исполнителя
  4. Create Order — создание заказа (холдирование денег заказчика)
  5. Make Decision — подтверждение/отказ (выплата или возврат)
  6. Get Order — проверка статуса заказа

Комиссии (взимаются с заказчика):
  - Комиссия Безопасных сделок: 0.80% от стоимости услуги
  - Комиссия платформы MVS-Work: 0.50% от стоимости услуги
  - Комиссия за эквайринг: 2.20% от (стоимость + комиссия БС + комиссия платформы)

Окружения:
  STAGE: https://stage-uapi.tochka.com
  PROD:  https://enter.tochka.com
"""

import os
import json
import uuid
import http.client
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# ── Константы комиссий ────────────────────────────────────────────────────────
MEDUSA_COMMISSION_RATE = Decimal("0.80")   # % — комиссия Точки
PLATFORM_COMMISSION_RATE = Decimal("0.50") # % — комиссия MVS-Work
ACQUIRING_COMMISSION_RATE = Decimal("2.20") # % — комиссия эквайринга


class MedusaAPIError(Exception):
    """Ошибка при работе с Medusa API"""
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class MedusaService:
    """
    Клиент для работы с API Безопасных сделок Точка Банка.
    
    Использует STAGE-окружение для тестирования (Sign-Key-Id / Sign-Body),
    PROD — для боевого режима.
    """

    def __init__(self):
        self.is_stage = os.getenv("MEDUSA_ENV", "stage").lower() == "stage"

        if self.is_stage:
            self.host = "stage-uapi.tochka.com"
            self.sign_key_id = os.getenv("MEDUSA_SIGN_KEY_ID", "7715014b-3d11-4c8a-add9-8cbc81364cea")
            self.sign_body = os.getenv("MEDUSA_SIGN_BODY", "12345")
        else:
            self.host = "enter.tochka.com"
            self.sign_key_id = os.getenv("MEDUSA_SIGN_KEY_ID", "")
            self.sign_body = os.getenv("MEDUSA_SIGN_BODY", "")

        self.base_path = "/uapi/medusa/v1.0"
        self.frontend_url = os.getenv("FRONTEND_URL", "https://mvs-work.ru")

        if not self.sign_key_id:
            logger.warning("[Medusa] MEDUSA_SIGN_KEY_ID не задан")

    # ── HTTP-слой ─────────────────────────────────────────────────────────────

    def _get_headers(self, method: str = "POST", body: str = "") -> Dict[str, str]:
        """
        Формирует заголовки для запроса.
        
        ВАЖНО: Sign-Body для GET-запросов должен быть подписью от ПУСТОГО тела.
        На STAGE: Sign-Body = "12345" для POST, пустая строка для GET.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Sign-Key-Id": self.sign_key_id,
        }

        if method.upper() == "GET":
            # GET — подпись от пустого тела
            headers["Sign-Body"] = "" if not self.is_stage else "12345"
        else:
            # POST/PATCH/DELETE — подпись от тела запроса
            headers["Sign-Body"] = self.sign_body

        return headers

    def _make_request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Выполняет HTTP-запрос к Medusa API.
        
        На STAGE используем HTTP (stage-uapi), на PROD — HTTPS (enter.tochka.com).
        """
        body = json.dumps(payload) if payload else ""

        if self.is_stage:
            conn = http.client.HTTPSConnection(self.host, timeout=30)
        else:
            conn = http.client.HTTPSConnection(self.host, timeout=30)

        full_path = f"{self.base_path}{path}"
        headers = self._get_headers(method, body)

        try:
            conn.request(method, full_path, body, headers)
            res = conn.getresponse()
            raw = res.read().decode("utf-8")

            logger.info(
                "[Medusa] %s %s → HTTP %s | Body: %s",
                method, full_path, res.status, raw[:500]
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
        """
        Рассчитать все комиссии для услуги.
        
        Алгоритм по документации Точки:
          1. Комиссия платформы = price × PLATFORM_COMMISSION_RATE / 100
          2. Комиссия Безопасных сделок = price × MEDUSA_COMMISSION_RATE / 100
          3. Комиссия за эквайринг = (price + platform + medusa) × ACQUIRING_RATE / 100
          4. Итого комиссий = platform + medusa + acquiring
          5. Заказчик платит = price + total_commission
          
        Возвращает dict с:
          - platform_commission: комиссия платформы
          - medusa_commission: комиссия Точки
          - acquiring_commission: комиссия эквайринга
          - total_commission: сумма всех комиссий (передаётся в Data.Services[].comission)
          - total_amount: итого к оплате заказчиком
        """
        price = Decimal(str(service_price))

        # 1. Комиссия платформы MVS-Work
        platform_commission = (price * PLATFORM_COMMISSION_RATE / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 2. Комиссия Безопасных сделок (Точки)
        medusa_commission = (price * MEDUSA_COMMISSION_RATE / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 3. Комиссия за эквайринг — от суммы всей транзакции
        transaction_sum = price + platform_commission + medusa_commission
        acquiring_commission = (transaction_sum * ACQUIRING_COMMISSION_RATE / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 4. Итого комиссий
        total_commission = platform_commission + medusa_commission + acquiring_commission

        # 5. Итого к оплате
        total_amount = price + total_commission

        return {
            "platform_commission": platform_commission,
            "medusa_commission": medusa_commission,
            "acquiring_commission": acquiring_commission,
            "total_commission": total_commission,     # → Data.Services[].comission
            "total_amount": total_amount,             # → что платит заказчик
            "service_price": price,                   # → Data.Services[].price
        }

    # ── 1. Получатели (Recipients) ────────────────────────────────────────────

    def create_recipient(self, recipient_ext_id: str, name: str) -> Dict[str, Any]:
        """
        Создать получателя (исполнителя) в системе Medusa.
        
        Args:
            recipient_ext_id: UUID — уникальный ID получателя на нашей стороне 
                              (обычно = user.id исполнителя)
            name: Имя получателя (для удобства просмотра)
        
        Returns:
            {"extId": "...", "name": "..."}
        """
        payload = {
            "extId": str(recipient_ext_id),
            "name": name[:128],  # max 128 символов
        }

        response = self._make_request("POST", "/recipients", payload)
        data = response.get("Data", response)

        logger.info("[Medusa] ✅ Получатель создан: %s (%s)", recipient_ext_id, name)
        return data

    def get_recipient(self, recipient_ext_id: str) -> Dict[str, Any]:
        """
        Получить информацию о получателе и его методах выплат.
        
        Returns:
            {
                "extId": "...",
                "name": "...",
                "PayoutMethods": [
                    {"extId": "card-uuid", "type": "CARD", "maskedPan": "****1234", ...}
                ]
            }
        """
        response = self._make_request("GET", f"/recipients/{recipient_ext_id}")
        return response.get("Data", response)

    def add_card_payout_method(
        self,
        recipient_ext_id: str,
        redirect_url: str,
        payout_method_ext_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Добавить карту для выплат исполнителю (токенизация).
        
        Возвращает URL формы, куда исполнитель вводит данные карты.
        После заполнения формы карта сохраняется в Точке.
        
        Args:
            recipient_ext_id: UUID получателя
            redirect_url: URL для редиректа после заполнения формы
            payout_method_ext_id: UUID карты на нашей стороне (генерируем если не передан)
        
        Returns:
            {"formUrl": "https://...", "payoutMethodExtId": "..."}
        """
        if not payout_method_ext_id:
            payout_method_ext_id = str(uuid.uuid4())

        payload = {
            "CardPayoutMethod": {
                "redirectUrl": redirect_url,
                "payoutMethodExtId": payout_method_ext_id,
            }
        }

        response = self._make_request(
            "POST",
            f"/recipients/{recipient_ext_id}/payout_methods/cards",
            payload,
        )

        data = response.get("Data", response)
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
        """Удалить карту исполнителя."""
        try:
            self._make_request(
                "DELETE",
                f"/recipients/{recipient_ext_id}/payout_methods/cards/{payout_method_ext_id}",
            )
            logger.info("[Medusa] ✅ Карта удалена: %s", payout_method_ext_id)
            return True
        except MedusaAPIError:
            return False

    # ── 2. Заказы (Orders) ────────────────────────────────────────────────────

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
        """
        Создать заказ в Medusa — холдирует деньги у заказчика.
        
        Заказчик получает ссылку на оплату. После оплаты деньги замораживаются
        до принятия решения (confirmed/rejected).
        
        Args:
            order_ext_id: UUID заказа (= deal.id)
            service_price: Цена услуги (чистая, без комиссий)
            recipient_ext_id: UUID получателя (= worker user_id)
            card_ext_id: UUID карты получателя (из Get Recipient → PayoutMethods[].extId)
            customer_email: Email заказчика (для чека)
            redirect_url: URL при успешной оплате
            redirect_fail_url: URL при неудачной оплате
            purpose: Назначение платежа
            payment_url_ttl: Время жизни ссылки (минуты)
            consumer_id: ID заказчика для сохранения карты (опционально)
        
        Returns:
            {
                "orderExtId": "...",
                "paymentUrl": "https://...",  — ссылка для заказчика
                "total_amount": Decimal,      — сумма к оплате
                "commission_details": {...}   — детали комиссий
            }
        """
        # Расчёт комиссий
        commission = self.calculate_commission(service_price)
        service_ext_id = str(uuid.uuid4())

        # Формируем payload по формату Medusa v1.0
        payload = {
            "orderExtId": str(order_ext_id),
            "orderCommission": str(commission["total_commission"]),
            "receiptEmail": customer_email,
            "IncomingPayment": {
                "type": "acquiring",
                "redirectUrl": redirect_url,
                "redirectFailUrl": redirect_fail_url,
                "paymentUrlTtl": payment_url_ttl,
                "purpose": purpose[:256],
            },
            "Services": [
                {
                    "extId": service_ext_id,
                    "price": str(commission["service_price"]),
                    "Recipient": {
                        "extId": str(recipient_ext_id),
                        "method": "CARD",
                        "cardExtId": str(card_ext_id),
                    },
                    "startDecision": "not_decided",
                }
            ],
        }

        # Опционально: ID заказчика для сохранения карты
        if consumer_id:
            payload["IncomingPayment"]["consumerId"] = str(consumer_id)

        response = self._make_request("POST", "/orders", payload)
        data = response.get("Data", response)

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
        """
        Получить информацию о заказе: статус, суммы, комиссии.
        
        Статусы заказа в Medusa:
          - created — создан, ожидает оплаты
          - paid — оплачен, деньги захолдированы
          - completed — исполнитель получил деньги
          - cancelled — отменён, деньги возвращены
        """
        response = self._make_request("GET", f"/orders/{order_ext_id}")
        return response.get("Data", response)

    def get_order_list(self, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        """Получить список заказов."""
        response = self._make_request("GET", f"/orders?offset={offset}&limit={limit}")
        return response.get("Data", response)

    def make_decision(
        self,
        order_ext_id: str,
        service_ext_id: str,
        decision: str,
    ) -> Dict[str, Any]:
        """
        Принять решение по услуге в заказе.
        
        Args:
            order_ext_id: UUID заказа
            service_ext_id: UUID услуги внутри заказа
            decision: "confirmed" (выплата исполнителю) или "rejected" (возврат заказчику)
        
        Returns:
            Ответ API Medusa
        """
        if decision not in ("confirmed", "rejected"):
            raise ValueError(f"decision должен быть 'confirmed' или 'rejected', получено: {decision}")

        payload = {
            "Decisions": [
                {
                    "serviceExtId": str(service_ext_id),
                    "decision": decision,
                }
            ]
        }

        response = self._make_request(
            "POST",
            f"/orders/{order_ext_id}/decisions",
            payload,
        )

        action = "подтверждён ✅" if decision == "confirmed" else "отклонён ❌"
        logger.info("[Medusa] Заказ %s — %s", order_ext_id, action)

        return response.get("Data", response)

    # ── 3. Sandbox-методы (только STAGE) ──────────────────────────────────────
    #
    # На тестовом окружении оплата не проходит через реальный эквайринг.
    # Нужно вручную вызывать sandbox-методы для эмуляции шагов.

    def sandbox_mark_order_paid(self, order_ext_id: str) -> Dict[str, Any]:
        """
        [STAGE] Эмулировать успешную оплату заказа заказчиком.
        
        Вызывать ПОСЛЕ того, как заказчик «оплатил» по ссылке
        (на STAGE — после открытия формы оплаты с тестовой картой).
        """
        if not self.is_stage:
            logger.warning("[Medusa] sandbox_mark_order_paid вызван в PROD-режиме, пропускаем")
            return {}

        payload = {"orderExtId": str(order_ext_id)}
        return self._make_request(
            "POST",
            "/sandbox/mark_order_paid_by_acquirer",
            payload,
        )

    def sandbox_mark_order_payment_failed(self, order_ext_id: str) -> Dict[str, Any]:
        """[STAGE] Эмулировать ошибку оплаты."""
        if not self.is_stage:
            return {}

        payload = {"orderExtId": str(order_ext_id)}
        return self._make_request(
            "POST",
            "/sandbox/mark_order_acquiring_payment_failed",
            payload,
        )

    def sandbox_proceed_payout(self, service_ext_id: str) -> Dict[str, Any]:
        """[STAGE] Эмулировать выплату исполнителю."""
        if not self.is_stage:
            return {}

        payload = {"serviceExtId": str(service_ext_id)}
        return self._make_request(
            "POST",
            "/sandbox/proceed_service_payout_to_recipient",
            payload,
        )

    def sandbox_proceed_refund(self, service_ext_id: str) -> Dict[str, Any]:
        """[STAGE] Эмулировать возврат заказчику."""
        if not self.is_stage:
            return {}

        payload = {"serviceExtId": str(service_ext_id)}
        return self._make_request(
            "POST",
            "/sandbox/proceed_refund",
            payload,
        )

    def sandbox_proceed_payout_commission(self, service_ext_id: str) -> Dict[str, Any]:
        """[STAGE] Эмулировать удержание комиссии за выплату."""
        if not self.is_stage:
            return {}

        payload = {"serviceExtId": str(service_ext_id)}
        return self._make_request(
            "POST",
            "/sandbox/proceed_service_payout_commission",
            payload,
        )

    def sandbox_proceed_acquiring_commission(self, order_ext_id: str) -> Dict[str, Any]:
        """[STAGE] Эмулировать удержание комиссии за эквайринг."""
        if not self.is_stage:
            return {}

        payload = {"orderExtId": str(order_ext_id)}
        return self._make_request(
            "POST",
            "/sandbox/proceed_acquiring_commission",
            payload,
        )

    def sandbox_move_platform_commission(self, order_ext_id: str) -> Dict[str, Any]:
        """[STAGE] Перевести комиссию платформы на счёт для комиссии."""
        if not self.is_stage:
            return {}

        payload = {"orderExtId": str(order_ext_id)}
        return self._make_request(
            "POST",
            "/sandbox/move_platform_commission_to_commission_account",
            payload,
        )

    def sandbox_proceed_platform_commission(self, order_ext_id: str) -> Dict[str, Any]:
        """[STAGE] Перевести комиссию платформы на расчётный счёт."""
        if not self.is_stage:
            return {}

        payload = {"orderExtId": str(order_ext_id)}
        return self._make_request(
            "POST",
            "/sandbox/proceed_platform_commission",
            payload,
        )

    def sandbox_full_cycle_after_decision(
        self,
        order_ext_id: str,
        service_ext_id: str,
        decision: str,
    ) -> None:
        """
        [STAGE] Выполнить весь цикл sandbox-шагов после принятия решения.
        
        На STAGE нужно вручную вызвать шаги 2-7:
          confirmed: оплата → выплата → комиссия выплаты → комиссия эквайринга → комиссия платформы
          rejected:  оплата → возврат → комиссия эквайринга
        """
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
            # Sandbox-ошибки не блокируют основной флоу
            logger.warning("[Medusa/Sandbox] ⚠️ Ошибка шага: %s", e)
