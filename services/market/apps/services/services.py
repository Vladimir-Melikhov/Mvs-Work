# services/market/apps/services/deal_service.py
import os
import requests
from decimal import Decimal
from django.utils import timezone
from django.db import transaction, IntegrityError
from .models import Deal, Transaction, Review
from django.conf import settings
from datetime import datetime, timedelta
import jwt
from .models import Service, Deal

class AIService:
    """
    AI-сервис для генерации СТРОГОГО ТЗ через YandexGPT.
    Ориентирован на профессиональную бизнес-аналитику.
    """
    
    @staticmethod
    def generate_tz(service_id: str, client_requirements: str) -> str:
        try:
            service = Service.objects.get(id=service_id)
            api_key = os.getenv('YANDEX_API_KEY')
            folder_id = os.getenv('YANDEX_FOLDER_ID')

            if not api_key or not folder_id:
                print("⚠️ [Market] Нет YANDEX_API_KEY или YANDEX_FOLDER_ID")
                return AIService._generate_mock_tz(client_requirements, service.price, service.title)

            # НОВЫЙ ПРОМПТ: Акцент на перевод в проф. плоскость без галлюцинаций
            system_instruction = """Ты — ведущий ИТ бизнес-аналитик. Твоя роль: структурировать хаотичные пожелания клиента в четкое техническое задание.

Твоя задача:
1. Конвертировать разговорную речь в профессиональную терминологию (вместо "сделать красиво" — "разработать визуальную концепцию согласно референсам").
2. Формулировать требования конкретно и без воды, но полными, красивыми предложениями.
3. Соблюдать точность: не придумывай технологии, инструменты или элементы дизайна, которые не упоминались.
4. Если в данных есть пробел, который критичен для работы — вежливо вынеси это в раздел уточняющих вопросов.
5. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО выдумывать технические детали (библиотеки, фреймворки, СУБД), если их нет в тексте.
6. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО выдумывать дизайн-решения (шрифты, цвета), если они не указаны явно.

Стиль: официально-деловой, технический, лаконичный.

Формат вывода (Markdown):
# Техническое задание: [Название услуги]
## 1. Концепция и цель проекта
(Опиши суть задачи профессиональным языком)
## 2. Технические параметры и условия исполнения
(Стек и требования, указанные исполнителем)
## 3. Функциональный объем работ
(Что конкретно должно быть реализовано на основе запроса заказчика)
## 4. Визуальные и контентные предпочтения
(Стилистика, цвета, референсы, если они были даны)
## 5. Перечень уточняющих вопросов
(Пункты, которые нужно прояснить перед стартом)"""

            freelancer_reqs = service.ai_template if service.ai_template else "Общие условия исполнения согласно профилю специалиста."
            
            user_content = f"""ИСХОДНЫЕ ДАННЫЕ ДЛЯ АНАЛИЗА:

1. ТРЕБОВАНИЯ ИСПОЛНИТЕЛЯ:
Услуга: {service.title}
Базовые условия: "{freelancer_reqs}"

2. ПОЖЕЛАНИЯ ЗАКАЗЧИКА:
Текст запроса: "{client_requirements}"

Задание: Сформируй на основе этих данных структурированное ТЗ. Не добавляй лишних функций, но используй профессиональный язык."""

            url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
            
            payload = {
                "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.4, # Чуть выше для красоты слога
                    "maxTokens": "4000"
                },
                "messages": [
                    {"role": "system", "text": system_instruction},
                    {"role": "user", "text": user_content}
                ]
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key {api_key}",
                "x-folder-id": folder_id
            }

            print(f"🔄 [Market] Генерация ТЗ (YandexGPT - Business Analyst Mode)...")
            
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 200:
                data = response.json()
                try:
                    generated_text = data['result']['alternatives'][0]['message']['text']
                    print(f"✅ [Market] ТЗ успешно сформировано ({len(generated_text)} симв.)")
                    return generated_text
                except (KeyError, IndexError) as e:
                    print(f"⚠️ Ошибка парсинга: {e}")
                    return AIService._generate_mock_tz(client_requirements, service.price, service.title)
            else:
                print(f"⚠️ Ошибка API ({response.status_code}): {response.text}")
                return AIService._generate_mock_tz(client_requirements, service.price, service.title)

        except Service.DoesNotExist:
            return AIService._generate_mock_tz(client_requirements, 0, "Проект")
        except Exception as e:
            print(f"🔥 Ошибка: {e}")
            return AIService._generate_mock_tz(client_requirements, 0, "Проект")

    @staticmethod
    def _generate_mock_tz(requirements: str, price: float, title: str) -> str:
        return f"# ТЗ: {title}\n\n## 1. Задача\n{requirements}\n\n_AI временно недоступен._"


class DealService:
    """
    СЕРВИС РАБОТЫ С ЗАКАЗАМИ (С ПОДДЕРЖКОЙ ЭСКРОУ И БЕЗ)
    """

    @staticmethod
    def _get_system_token() -> str:
        from .jwt_service import ServiceJWT
        return ServiceJWT.generate_service_token('market-service', expires_minutes=5)

    @staticmethod
    @transaction.atomic
    def create_deal(chat_room_id: str, client_id: str, worker_id: str,
                    title: str, description: str, price: Decimal,
                    auth_token: str, is_escrow: bool = True):
        try:
            deal, created = Deal.objects.select_for_update().get_or_create(
                client_id=client_id,
                worker_id=worker_id,
                status__in=['pending', 'accepted', 'paid', 'delivered', 'dispute'],
                defaults={
                    'chat_room_id': chat_room_id,
                    'title': title,
                    'description': description,
                    'price': int(price ),
                    'status': 'pending',
                    'was_delivered': False,
                    'is_escrow': is_escrow,
                }
            )

            if not created:
                raise ValueError(f"У вас уже есть активный заказ с этим исполнителем. ID заказа: {deal.id}")

            DealService._send_text_message(
                chat_room_id=chat_room_id,
                sender_id=client_id,
                text=f"📋 ТЕХНИЧЕСКОЕ ЗАДАНИЕ\n\n{description}",
                auth_token=auth_token
            )

            DealService._send_deal_card(deal, client_id, 'created', auth_token)
            return deal

        except IntegrityError:
            raise ValueError("Не удалось создать заказ. У вас уже есть активный заказ с этим исполнителем.")

    # ── Неэскроу: принятие заказа исполнителем ────────────────────────────────

    @staticmethod
    @transaction.atomic
    def worker_accept(deal: Deal, worker_id: str, auth_token: str):
        """Исполнитель принимает неэскроу-заказ и приступает к работе"""
        if str(worker_id) != str(deal.worker_id):
            raise ValueError("Принять заказ может только исполнитель")

        if deal.is_escrow:
            raise ValueError("Это действие доступно только для заказов без безопасной сделки")

        if deal.status != 'pending':
            raise ValueError(f"Нельзя принять заказ в статусе '{deal.status}'")

        deal.status = 'accepted'
        deal.save()

        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=worker_id,
            text="⚡ ЗАКАЗ ПРИНЯТ\n\nИсполнитель приступил к выполнению заказа.\n\nВы можете оплатить заказ в любой момент.",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, worker_id, 'accepted', auth_token)
        return deal

    # ── Изменение цены ─────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def update_price(deal: Deal, worker_id: str, new_price: Decimal, auth_token: str):
        if str(worker_id) != str(deal.worker_id):
            raise ValueError("Изменить цену может только исполнитель")

        if deal.status != 'pending':
            raise ValueError(f"Нельзя изменить цену в статусе '{deal.status}'")

        if new_price <= 0:
            raise ValueError("Цена должна быть больше нуля")

        old_price = int(deal.price)
        deal.price = int(new_price)
        deal.save()

        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=worker_id,
            text=f"💰 ЦЕНА ИЗМЕНЕНА\n\nБыло: {old_price}₽\nСтало: {int(new_price)}₽",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, worker_id, 'price_updated', auth_token)
        return deal

    # ── Оплата ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def pay_deal(deal: Deal, client_id: str, auth_token: str):
        if str(client_id) != str(deal.client_id):
            raise ValueError("Оплатить может только клиент")

        if deal.is_escrow:
            if deal.status != 'pending':
                raise ValueError(f"Нельзя оплатить заказ в статусе '{deal.status}'")
        else:
            # Неэскроу: оплата доступна после принятия исполнителем
            if deal.status not in ['pending', 'accepted']:
                raise ValueError(f"Нельзя оплатить заказ в статусе '{deal.status}'")

        Transaction.objects.create(
            deal=deal,
            amount=deal.price,
            commission=0,
            status='held',
            payment_provider='stub'
        )

        deal.status = 'paid'
        deal.paid_at = timezone.now()
        deal.save()

        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=client_id,
            text=f"💳 ЗАКАЗ ОПЛАЧЕН\n\nСумма: {int(deal.price)}₽\n\nТеперь исполнитель может сдать работу.",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, client_id, 'paid', auth_token)
        return deal

    # ── Сдача работы ───────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def deliver_work(deal: Deal, worker_id: str, delivery_message: str, auth_token: str):
        if str(worker_id) != str(deal.worker_id):
            raise ValueError("Сдать работу может только исполнитель")

        if deal.is_escrow:
            if deal.status != 'paid':
                raise ValueError(f"Нельзя сдать работу в статусе '{deal.status}'")
        else:
            # Неэскроу: можно сдать после принятия или после оплаты
            if deal.status not in ['accepted', 'paid']:
                raise ValueError(f"Нельзя сдать работу в статусе '{deal.status}'")

        deal.status = 'delivered'
        deal.delivered_at = timezone.now()
        deal.delivery_message = delivery_message
        deal.was_delivered = True
        deal.save()

        DealService._send_delivery_message(deal, worker_id, delivery_message, auth_token)
        DealService._send_deal_card(deal, worker_id, 'delivered', auth_token)
        return deal

    @staticmethod
    def _send_delivery_message(deal: Deal, sender_id: str, delivery_message: str, auth_token: str):
        try:
            url = f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/{deal.chat_room_id}/send_deal_message/"

            attachment_data = []
            for att in deal.delivery_attachments.all():
                if att.file:
                    attachment_data.append({
                        'id': str(att.id),
                        'filename': att.filename,
                        'file_size': att.file_size,
                        'content_type': att.content_type or 'application/octet-stream',
                        'url': att.file.url
                    })

            payload = {
                'sender_id': str(sender_id),
                'message_type': 'text',
                'text': f"📦 РЕЗУЛЬТАТ РАБОТЫ\n\n{delivery_message}",
                'deal_data': None,
                'is_system': True,
                'attachments': attachment_data
            }

            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, json=payload, timeout=5)

            if response.status_code != 200:
                print(f"⚠️ Ошибка отправки сообщения с файлами: {response.text[:200]}")

        except Exception as e:
            print(f"🔥 Error sending delivery message: {e}")

    # ── Доработка ──────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def request_revision(deal: Deal, client_id: str, revision_reason: str, auth_token: str):
        if str(client_id) != str(deal.client_id):
            raise ValueError("Запросить доработку может только клиент")

        if deal.status != 'delivered':
            raise ValueError("Доработку можно запросить только после сдачи")

        if deal.revision_count >= deal.max_revisions:
            raise ValueError(f"Исчерпан лимит доработок ({deal.max_revisions})")

        # Возвращаем в статус "в работе": для эскроу — paid, для неэскроу — accepted/paid
        if deal.is_escrow:
            deal.status = 'paid'
        else:
            deal.status = 'accepted' if not deal.paid_at else 'paid'

        deal.revision_count += 1
        deal.save()

        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=client_id,
            text=f"🔄 ЗАПРОС НА ДОРАБОТКУ ({deal.revision_count}/{deal.max_revisions})\n\n{revision_reason}",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, client_id, 'revision', auth_token)
        return deal

    # ── Спор ───────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def open_dispute(deal: Deal, client_id: str, dispute_reason: str, auth_token: str):
        if str(client_id) != str(deal.client_id):
            raise ValueError("Открыть спор может только клиент")

        if deal.status != 'delivered':
            raise ValueError("Спор можно открыть только после сдачи работы")

        deal.status = 'dispute'
        deal.dispute_client_reason = dispute_reason
        deal.dispute_created_at = timezone.now()
        deal.save()

        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=client_id,
            text=f"⚠️ ОТКРЫТ СПОР\n\nПретензия клиента:\n{dispute_reason}",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, client_id, 'dispute_opened', auth_token)
        return deal

    @staticmethod
    @transaction.atomic
    def worker_refund(deal: Deal, worker_id: str, auth_token: str):
        if str(worker_id) != str(deal.worker_id):
            raise ValueError("Только исполнитель может вернуть деньги")

        if deal.status != 'dispute':
            raise ValueError("Возврат возможен только в статусе спора")

        if deal.dispute_worker_defense:
            raise ValueError("Нельзя вернуть деньги после подачи защиты")

        transaction_obj = deal.transactions.filter(status='held').first()
        if transaction_obj:
            transaction_obj.status = 'refunded'
            transaction_obj.save()

        deal.status = 'cancelled'
        deal.cancelled_at = timezone.now()
        deal.cancellation_reason = "Исполнитель вернул деньги в споре"
        deal.dispute_winner = 'client'
        deal.dispute_resolved_at = timezone.now()
        deal.save()

        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=worker_id,
            text=f"💰 ДЕНЬГИ ВОЗВРАЩЕНЫ\n\nИсполнитель согласился с претензией и вернул средства клиенту.",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, worker_id, 'refunded', auth_token)
        return deal

    @staticmethod
    @transaction.atomic
    def worker_defend(deal: Deal, worker_id: str, defense_text: str, auth_token: str):
        if str(worker_id) != str(deal.worker_id):
            raise ValueError("Только исполнитель может подать защиту")

        if deal.status != 'dispute':
            raise ValueError("Защиту можно подать только в статусе спора")

        if deal.dispute_worker_defense:
            raise ValueError("Защита уже подана")

        deal.dispute_worker_defense = defense_text
        deal.save()

        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=worker_id,
            text=f"🛡️ ЗАЩИТА ПОДАНА\n\nИсполнитель оспорил претензию:\n{defense_text}\n\n⏳ Спор передан администратору.",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, worker_id, 'defense_submitted', auth_token)
        DealService._send_to_telegram_admin(deal)

        return deal

    # ── Административное разрешение спора ─────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def admin_resolve_dispute(deal: Deal, winner: str, admin_comment: str = '', auth_token: str = ''):
        if deal.status != 'dispute':
            raise ValueError("Разрешить можно только активный спор")

        if not deal.dispute_worker_defense:
            raise ValueError("Нельзя разрешить спор до подачи защиты")

        if winner not in ['client', 'worker']:
            raise ValueError("winner должен быть 'client' или 'worker'")

        deal.dispute_winner = winner
        deal.dispute_resolved_at = timezone.now()

        transaction_obj = deal.transactions.filter(status='held').first()

        if winner == 'client':
            if transaction_obj:
                transaction_obj.status = 'refunded'
                transaction_obj.save()

            deal.status = 'cancelled'
            deal.cancelled_at = timezone.now()
            deal.cancellation_reason = f"Спор разрешен в пользу клиента. {admin_comment}"

        else:
            if transaction_obj:
                transaction_obj.status = 'captured'
                transaction_obj.save()

            deal.status = 'completed'
            deal.completed_at = timezone.now()
            deal.completion_message = f"Спор разрешен в пользу исполнителя. {admin_comment}"

        deal.save()

        system_token = DealService._get_system_token()
        action_type = 'admin_resolved_client' if winner == 'client' else 'admin_resolved_worker'

        winner_text = 'клиента' if winner == 'client' else 'исполнителя'
        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=deal.client_id,
            text=f"🎉 СПОР РАЗРЕШЁН\n\nРешение администратора: в пользу {winner_text}.",
            auth_token=system_token
        )

        DealService._send_deal_card(deal, deal.client_id, action_type, system_token)

        return deal

    # ── Завершение ─────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def complete_deal(deal: Deal, client_id: str, rating: int, comment: str, auth_token: str):
        if str(client_id) != str(deal.client_id):
            raise ValueError("Завершить заказ может только клиент")

        if deal.status != 'delivered':
            raise ValueError("Завершить можно только сданный заказ")

        transaction_obj = deal.transactions.filter(status='held').first()
        if transaction_obj:
            transaction_obj.status = 'captured'
            transaction_obj.save()

        deal.status = 'completed'
        deal.completed_at = timezone.now()
        deal.completion_message = comment
        deal.save()

        Review.objects.create(
            deal=deal,
            rating=rating,
            comment=comment,
            reviewer_id=client_id,
            reviewee_id=deal.worker_id
        )

        DealService._send_deal_card(deal, client_id, 'completed', auth_token)
        return deal

    # ── Отмена ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def cancel_deal(deal: Deal, canceller_id: str, reason: str, auth_token: str):
        if str(canceller_id) not in [str(deal.client_id), str(deal.worker_id)]:
            raise ValueError("Вы не участник заказа")

        if deal.status == 'completed':
            raise ValueError("Нельзя отменить завершённый заказ")

        if deal.was_delivered:
            raise ValueError("Нельзя отменить заказ после сдачи работы. Используйте 'Открыть спор' или 'Запросить доработку'.")

        if deal.status in ['delivered', 'dispute']:
            raise ValueError("После сдачи работы отмена невозможна. Используйте спор.")

        if deal.status in ['paid']:
            transaction_obj = deal.transactions.filter(status='held').first()
            if transaction_obj:
                transaction_obj.status = 'refunded'
                transaction_obj.save()

        deal.status = 'cancelled'
        deal.cancelled_at = timezone.now()
        deal.cancellation_reason = reason
        deal.save()

        DealService._send_deal_card(deal, canceller_id, 'cancelled', auth_token)
        return deal

    # ── Вспомогательные методы ─────────────────────────────────────────────────

    @staticmethod
    def _send_text_message(chat_room_id: str, sender_id: str, text: str, auth_token: str):
        try:
            url = f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/{chat_room_id}/send_deal_message/"

            payload = {
                'sender_id': str(sender_id),
                'message_type': 'text',
                'text': text,
                'deal_data': None,
                'is_system': True
            }

            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            }

            requests.post(url, headers=headers, json=payload, timeout=5)

        except Exception as e:
            print(f"🔥 Error sending text message: {e}")

    @staticmethod
    def _send_deal_card(deal: Deal, sender_id: str, action_type: str, auth_token: str):
        try:
            if not auth_token:
                auth_token = DealService._get_system_token()

            url = f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/{deal.chat_room_id}/send_deal_message/"

            delivery_attachments = []
            for att in deal.delivery_attachments.all():
                if att.file:
                    delivery_attachments.append({
                        'id': str(att.id),
                        'filename': att.filename,
                        'file_size': att.file_size,
                        'url': att.file.url
                    })

            deal_data = {
                'deal_id': str(deal.id),
                'title': deal.title,
                'price': int(deal.price),
                'status': deal.status,
                'is_escrow': deal.is_escrow,
                'client_id': str(deal.client_id),
                'worker_id': str(deal.worker_id),
                'revision_count': deal.revision_count,
                'max_revisions': deal.max_revisions,
                'delivery_message': deal.delivery_message or '',
                'delivery_attachments': delivery_attachments,
                'can_pay': deal.can_pay,
                'can_deliver': deal.can_deliver,
                'can_request_revision': deal.can_request_revision,
                'can_complete': deal.can_complete,
                'can_cancel': deal.can_cancel,
                'can_update_price': deal.can_update_price,
                'can_open_dispute': deal.can_open_dispute,
                'can_worker_refund': deal.can_worker_refund,
                'can_worker_defend': deal.can_worker_defend,
                'can_worker_accept': deal.can_worker_accept,
                'is_dispute_pending_admin': deal.is_dispute_pending_admin,
                'dispute_client_reason': deal.dispute_client_reason or '',
                'dispute_worker_defense': deal.dispute_worker_defense or '',
                'dispute_created_at': deal.dispute_created_at.isoformat() if deal.dispute_created_at else None,
                'dispute_resolved_at': deal.dispute_resolved_at.isoformat() if deal.dispute_resolved_at else None,
                'dispute_winner': deal.dispute_winner or '',
                'status_display': DealService._get_status_display(deal),
                'dispute_result': DealService._get_dispute_result(deal),
                'created_at': deal.created_at.isoformat() if deal.created_at else None,
            }

            message_texts = {
                'created': f'📋 Создан заказ: {deal.title}',
                'accepted': '⚡ Исполнитель принял заказ и приступил к работе',
                'paid': f'💳 Заказ оплачен! {int(deal.price)}₽',
                'delivered': '📦 Работа сдана на проверку',
                'revision': f'🔄 Запрошена доработка ({deal.revision_count}/{deal.max_revisions})',
                'completed': '🎉 Заказ завершён!',
                'cancelled': '❌ Заказ отменён',
                'price_updated': f'💰 Цена изменена: {int(deal.price)}₽',
                'dispute_opened': '⚠️ Открыт спор',
                'defense_submitted': '🛡️ Защита подана, ждем админа',
                'refunded': '💰 Деньги возвращены клиенту',
                'admin_resolved_client': '🎉 Спор разрешён: деньги возвращены клиенту',
                'admin_resolved_worker': '🎉 Спор разрешён: оплата выполнена исполнителю',
            }

            text = message_texts.get(action_type, '📋 Обновление заказа')

            payload = {
                'sender_id': str(sender_id),
                'message_type': 'deal_card',
                'text': text,
                'deal_data': deal_data
            }

            if deal.last_message_id:
                payload['update_message_id'] = str(deal.last_message_id)

            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, json=payload, timeout=5)

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('status') == 'success':
                    message_id = response_data.get('data', {}).get('id')
                    if message_id and not deal.last_message_id:
                        deal.last_message_id = message_id
                        deal.save(update_fields=['last_message_id'])
            else:
                print(f"⚠️ _send_deal_card HTTP error {response.status_code}: {response.text[:300]}")

        except Exception as e:
            print(f"🔥 Error sending deal card: {e}")

    @staticmethod
    def _send_to_telegram_admin(deal: Deal):
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            admin_id = os.getenv('TELEGRAM_ADMIN_ID')
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')

            if not bot_token or not admin_id:
                print("⚠️ TELEGRAM_BOT_TOKEN или TELEGRAM_ADMIN_ID не настроены")
                return

            message = f"""
🚨 <b>НОВЫЙ СПОР #{deal.id}</b>

📋 <b>Заказ:</b> {deal.title}
💰 <b>Сумма:</b> {int(deal.price)}₽

👤 <b>ПРЕТЕНЗИЯ КЛИЕНТА:</b>
{deal.dispute_client_reason}

🛡️ <b>ЗАЩИТА ИСПОЛНИТЕЛЯ:</b>
{deal.dispute_worker_defense}

🔗 <a href="{frontend_url}/admin/disputes/{deal.id}">Разрешить спор</a>
            """

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': admin_id,
                'text': message.strip(),
                'parse_mode': 'HTML'
            }

            response = requests.post(url, json=data, timeout=10)

            if response.status_code == 200:
                print(f"✅ Уведомление о споре {deal.id} отправлено в Telegram")
            else:
                print(f"⚠️ Ошибка отправки в Telegram: {response.text}")

        except Exception as e:
            print(f"🔥 Error sending to Telegram: {e}")

    @staticmethod
    def _get_status_display(deal: Deal) -> str:
        status_map = {
            'pending': 'Ожидает оплаты',
            'accepted': 'Исполнитель принял заказ',
            'paid': 'В работе',
            'delivered': 'На проверке',
            'dispute': 'В споре',
            'completed': 'Завершён',
            'cancelled': 'Отменён',
        }

        base_status = status_map.get(deal.status, deal.status)

        if deal.dispute_winner:
            if deal.dispute_winner == 'client':
                if deal.status == 'cancelled':
                    return 'Отменён (спор - победа клиента)'
                return f'{base_status} (спор - победа клиента)'
            elif deal.dispute_winner == 'worker':
                if deal.status == 'completed':
                    return 'Завершён (спор - победа исполнителя)'
                return f'{base_status} (спор - победа исполнителя)'

        return base_status

    @staticmethod
    def _get_dispute_result(deal: Deal):
        if not deal.dispute_winner:
            return None

        return {
            'winner': deal.dispute_winner,
            'winner_text': 'клиента' if deal.dispute_winner == 'client' else 'исполнителя',
            'resolved_at': deal.dispute_resolved_at.isoformat() if deal.dispute_resolved_at else None,
            'message': f"Спор разрешен в пользу {'клиента' if deal.dispute_winner == 'client' else 'исполнителя'}"
        }
