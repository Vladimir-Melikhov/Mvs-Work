from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import Deal, Transaction, Review
import requests
from django.conf import settings


class DealService:
    """
    УПРОЩЁННЫЙ СЕРВИС РАБОТЫ С ЗАКАЗАМИ
    
    ✅ С СИСТЕМОЙ СПОРА для защиты от отмены после сдачи
    ✅ БЕЗ MARKDOWN в текстовых сообщениях
    """

    COMMISSION_RATE = Decimal('0.08')

    @staticmethod
    def check_active_deal(client_id: str, worker_id: str):
        """Проверка наличия активного заказа между двумя пользователями"""
        active_deal = Deal.objects.filter(
            client_id=client_id,
            worker_id=worker_id,
            status__in=['pending', 'paid', 'delivered']
        ).first()
        
        return active_deal

    @staticmethod
    @transaction.atomic
    def create_deal(chat_room_id: str, client_id: str, worker_id: str, 
                    title: str, description: str, price: Decimal, auth_token: str):
        """
        Создать новый заказ
        Проверяет наличие активных заказов
        """
        # Проверка активного заказа
        active_deal = DealService.check_active_deal(client_id, worker_id)
        if active_deal:
            raise ValueError(f"У вас уже есть активный заказ с этим исполнителем. ID заказа: {active_deal.id}")

        # Создаём заказ
        deal = Deal.objects.create(
            chat_room_id=chat_room_id,
            client_id=client_id,
            worker_id=worker_id,
            title=title,
            description=description,
            price=price,
            status='pending'
        )

        # ✅ ИСПРАВЛЕНО: Отправляем ТЗ БЕЗ MARKDOWN
        DealService._send_text_message(
            chat_room_id=chat_room_id,
            sender_id=client_id,
            text=f"ТЕХНИЧЕСКОЕ ЗАДАНИЕ\n\n{description}",
            auth_token=auth_token
        )

        # Отправляем карточку заказа
        DealService._send_deal_card(deal, client_id, 'created', auth_token)

        return deal

    @staticmethod
    @transaction.atomic
    def update_price(deal: Deal, worker_id: str, new_price: Decimal, auth_token: str):
        """
        Изменить цену заказа (только исполнитель, только до оплаты)
        """
        if str(worker_id) != str(deal.worker_id):
            raise ValueError("Изменить цену может только исполнитель")

        if deal.status != 'pending':
            raise ValueError(f"Нельзя изменить цену в статусе '{deal.status}'")

        if new_price <= 0:
            raise ValueError("Цена должна быть больше нуля")

        old_price = deal.price
        deal.price = new_price
        deal.save()

        # ✅ ИСПРАВЛЕНО: БЕЗ MARKDOWN
        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=worker_id,
            text=f"ЦЕНА ИЗМЕНЕНА\n\nБыло: {old_price}₽\nСтало: {new_price}₽",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, worker_id, 'price_updated', auth_token)

        return deal

    @staticmethod
    @transaction.atomic
    def pay_deal(deal: Deal, client_id: str, auth_token: str):
        """Оплата заказа (заглушка)"""
        if str(client_id) != str(deal.client_id):
            raise ValueError("Оплатить может только клиент")

        if deal.status != 'pending':
            raise ValueError(f"Нельзя оплатить заказ в статусе '{deal.status}'")

        # Создаём транзакцию холдирования
        commission = deal.price * DealService.COMMISSION_RATE
        total = deal.price + commission

        Transaction.objects.create(
            deal=deal,
            amount=total,
            commission=commission,
            status='held',
            payment_provider='stub'
        )

        # Обновляем статус
        deal.status = 'paid'
        deal.paid_at = timezone.now()
        deal.save()

        DealService._send_deal_card(deal, client_id, 'paid', auth_token)

        return deal

    @staticmethod
    @transaction.atomic
    def deliver_work(deal: Deal, worker_id: str, delivery_message: str, auth_token: str):
        """Сдача работы исполнителем"""
        if str(worker_id) != str(deal.worker_id):
            raise ValueError("Сдать работу может только исполнитель")

        if deal.status != 'paid':
            raise ValueError(f"Нельзя сдать работу в статусе '{deal.status}'")

        deal.status = 'delivered'
        deal.delivered_at = timezone.now()
        deal.delivery_message = delivery_message
        deal.save()

        # ✅ ИСПРАВЛЕНО: БЕЗ MARKDOWN
        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=worker_id,
            text=f"РЕЗУЛЬТАТ РАБОТЫ\n\n{delivery_message}",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, worker_id, 'delivered', auth_token)

        return deal

    @staticmethod
    @transaction.atomic
    def request_revision(deal: Deal, client_id: str, revision_reason: str, auth_token: str):
        """Запрос доработки"""
        if str(client_id) != str(deal.client_id):
            raise ValueError("Запросить доработку может только клиент")

        if deal.status != 'delivered':
            raise ValueError("Доработку можно запросить только после сдачи")

        if deal.revision_count >= deal.max_revisions:
            raise ValueError(f"Исчерпан лимит доработок ({deal.max_revisions})")

        deal.status = 'paid'
        deal.revision_count += 1
        deal.save()

        # ✅ ИСПРАВЛЕНО: БЕЗ MARKDOWN
        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=client_id,
            text=f"ЗАПРОС НА ДОРАБОТКУ ({deal.revision_count}/{deal.max_revisions})\n\n{revision_reason}",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, client_id, 'revision', auth_token)

        return deal

    @staticmethod
    @transaction.atomic
    def complete_deal(deal: Deal, client_id: str, rating: int, comment: str, auth_token: str):
        """
        Завершение заказа клиентом
        Создание отзыва
        Перевод средств исполнителю
        """
        if str(client_id) != str(deal.client_id):
            raise ValueError("Завершить заказ может только клиент")

        if deal.status != 'delivered':
            raise ValueError("Завершить можно только сданный заказ")

        # Перевод средств
        transaction_obj = deal.transactions.filter(status='held').first()
        if transaction_obj:
            transaction_obj.status = 'captured'
            transaction_obj.save()

        # Завершаем заказ
        deal.status = 'completed'
        deal.completed_at = timezone.now()
        deal.completion_message = comment
        deal.save()

        # Создаём отзыв
        Review.objects.create(
            deal=deal,
            rating=rating,
            comment=comment,
            reviewer_id=client_id,
            reviewee_id=deal.worker_id
        )

        DealService._send_deal_card(deal, client_id, 'completed', auth_token)

        return deal

    # ============================================================
    # ✅ НОВЫЕ МЕТОДЫ: СИСТЕМА СПОРА
    # ============================================================

    @staticmethod
    @transaction.atomic
    def request_dispute(deal: Deal, initiator_id: str, reason: str, auth_token: str):
        """
        Открыть спор (первый шаг перед отменой после оплаты)
        
        Логика:
        - Любая сторона может открыть спор
        - Вторая сторона должна согласиться на отмену
        - Таймер 24 часа для ответа
        """
        if str(initiator_id) not in [str(deal.client_id), str(deal.worker_id)]:
            raise ValueError("Вы не участник заказа")

        if deal.status not in ['paid', 'delivered']:
            raise ValueError("Спор можно открыть только для оплаченного заказа")

        if deal.dispute_status != 'none':
            raise ValueError("Спор уже открыт")

        # Открываем спор
        deal.dispute_status = 'requested'
        deal.dispute_reason = reason
        deal.dispute_initiator_id = initiator_id
        deal.dispute_created_at = timezone.now()
        deal.save()

        # Уведомление в чат
        initiator_name = "Клиент" if str(initiator_id) == str(deal.client_id) else "Исполнитель"
        
        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=initiator_id,
            text=f"СПОР ОТКРЫТ\n\n{initiator_name} предлагает отменить заказ.\n\nПричина: {reason}\n\nОбе стороны должны согласиться на отмену в течение 24 часов.",
            auth_token=auth_token
        )

        DealService._send_deal_card(deal, initiator_id, 'dispute_opened', auth_token)

        return deal

    @staticmethod
    @transaction.atomic
    def cancel_deal(deal: Deal, canceller_id: str, reason: str, auth_token: str):
        """
        Отменить заказ
        
        ✅ ОБНОВЛЁННАЯ ЛОГИКА:
        - До оплаты (pending) - свободная отмена
        - После оплаты (paid/delivered) - только через спор с согласием обеих сторон
        """
        if str(canceller_id) not in [str(deal.client_id), str(deal.worker_id)]:
            raise ValueError("Вы не участник заказа")

        if deal.status == 'completed':
            raise ValueError("Нельзя отменить завершённый заказ")

        # ✅ До оплаты - свободная отмена
        if deal.status == 'pending':
            deal.status = 'cancelled'
            deal.cancelled_at = timezone.now()
            deal.cancellation_reason = reason
            deal.save()

            DealService._send_deal_card(deal, canceller_id, 'cancelled', auth_token)
            return deal

        # ✅ После оплаты - только через спор
        if deal.status in ['paid', 'delivered']:
            
            # Проверяем наличие спора
            if deal.dispute_status == 'none':
                raise ValueError("Сначала откройте спор для безопасной отмены заказа")
            
            # Проверяем, что отменяет НЕ инициатор спора (т.е. вторая сторона согласилась)
            if str(canceller_id) == str(deal.dispute_initiator_id):
                raise ValueError("Ожидается согласие второй стороны на отмену")

            # Обе стороны согласились - отменяем и возвращаем деньги
            transaction_obj = deal.transactions.filter(status='held').first()
            if transaction_obj:
                transaction_obj.status = 'refunded'
                transaction_obj.save()

            deal.status = 'cancelled'
            deal.cancelled_at = timezone.now()
            deal.cancellation_reason = f"Спор: {deal.dispute_reason}. Отмена: {reason}"
            deal.dispute_status = 'resolved'
            deal.save()

            DealService._send_text_message(
                chat_room_id=deal.chat_room_id,
                sender_id=canceller_id,
                text=f"ЗАКАЗ ОТМЕНЁН\n\nОбе стороны согласились на отмену. Средства возвращены клиенту.",
                auth_token=auth_token
            )

            DealService._send_deal_card(deal, canceller_id, 'cancelled', auth_token)
            return deal

        raise ValueError("Невозможно отменить заказ в текущем статусе")

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _send_text_message(chat_room_id: str, sender_id: str, text: str, auth_token: str):
        """Отправка обычного текстового сообщения в чат"""
        try:
            url = f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/{chat_room_id}/send_deal_message/"
            
            payload = {
                'sender_id': str(sender_id),
                'message_type': 'text',
                'text': text,
                'deal_data': None
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
        """Отправка/обновление карточки заказа в чате"""
        try:
            url = f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/{deal.chat_room_id}/send_deal_message/"
            
            commission = float(deal.price * DealService.COMMISSION_RATE)
            total = float(deal.price) + commission
            
            deal_data = {
                'deal_id': str(deal.id),
                'title': deal.title,
                'price': str(deal.price),
                'commission': f"{commission:.2f}",
                'total': f"{total:.2f}",
                'status': deal.status,
                'client_id': str(deal.client_id),
                'worker_id': str(deal.worker_id),
                'revision_count': deal.revision_count,
                'max_revisions': deal.max_revisions,
                'delivery_message': deal.delivery_message or '',
                'can_pay': deal.can_pay,
                'can_deliver': deal.can_deliver,
                'can_request_revision': deal.can_request_revision,
                'can_complete': deal.can_complete,
                'can_cancel': deal.can_cancel,
                'can_update_price': deal.can_update_price,
                
                # ✅ НОВОЕ: Данные спора
                'dispute_status': deal.dispute_status,
                'dispute_reason': deal.dispute_reason or '',
                'dispute_initiator_id': str(deal.dispute_initiator_id) if deal.dispute_initiator_id else None,
            }
            
            message_texts = {
                'created': f'📋 Создан заказ: {deal.title}',
                'paid': f'💳 Заказ оплачен! {total}₽',
                'delivered': '📦 Работа сдана на проверку',
                'revision': f'🔄 Запрошена доработка ({deal.revision_count}/{deal.max_revisions})',
                'completed': '🎉 Заказ завершён!',
                'cancelled': '❌ Заказ отменён',
                'price_updated': f'💰 Цена изменена: {deal.price}₽',
                'dispute_opened': '⚠️ Открыт спор по заказу',
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
            
        except Exception as e:
            print(f"🔥 Error sending deal card: {e}")
