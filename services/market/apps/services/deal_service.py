from decimal import Decimal
from django.utils import timezone
from .models import Deal, Transaction, Service
import requests
from django.conf import settings


class DealService:
    """
    УЛУЧШЕННАЯ ВЕРСИЯ с поддержкой множественных заказов в одном чате
    
    1. Предложение условий (можно менять ДО оплаты)
    2. Согласование обеими сторонами
    3. Оплата (после этого условия ЗАМОРОЖЕНЫ)
    4. Выполнение работы
    5. Сдача работы
    6. Проверка + возможные доработки
    7. Принятие и завершение

    ЗАЩИТА:
    - После оплаты нельзя менять цену/ТЗ напрямую
    - Изменения возможны только через отмену + новый заказ
    - Или через механизм "запроса изменений" (требует согласия)
    """

    COMMISSION_RATE = Decimal('0.05')

    @staticmethod
    def get_or_create_deal(chat_room_id: str, client_id: str, worker_id: str) -> Deal:
        """
        ✅ ИСПРАВЛЕНО: Теперь всегда создаем НОВЫЙ заказ
        Старая логика с get_or_create не давала создать второй заказ
        """
        deal = Deal.objects.create(
            chat_room_id=chat_room_id,
            client_id=client_id,
            worker_id=worker_id,
            title='Новый заказ',
            description='Условия обсуждаются',
            price=Decimal('0.00'),
            status='draft'
        )
        return deal
    
    # ============================================================
    # ЭТАП 1: ПРЕДЛОЖЕНИЕ И СОГЛАСОВАНИЕ (ДО ОПЛАТЫ)
    # ============================================================
    
    @staticmethod
    def propose_terms(deal: Deal, proposer_id: str, title: str, description: str, price: Decimal, auth_token: str):
        """
        Предложить или изменить условия заказа.
        
        ПРАВИЛА:
        - Можно менять ТОЛЬКО до оплаты
        - Кто предложил → автоматически согласен
        - Вторая сторона должна согласиться заново
        """
        # ✅ ЗАЩИТА: Нельзя менять после оплаты
        if deal.payment_completed:
            raise ValueError("❌ Нельзя изменить условия после оплаты. Отмените заказ и создайте новый.")
        
        if deal.status not in ['draft', 'pending_payment']:
            raise ValueError(f"❌ Нельзя изменить условия в статусе '{deal.status}'")
        
        # Проверка прав
        if str(proposer_id) not in [str(deal.client_id), str(deal.worker_id)]:
            raise ValueError("❌ Вы не участник этого заказа")
        
        # Сохраняем в историю предыдущую версию
        if deal.price > 0:
            deal.history.append({
                'timestamp': timezone.now().isoformat(),
                'action': 'terms_changed',
                'by': str(proposer_id),
                'old_title': deal.title,
                'old_price': str(deal.price),
            })
        
        # Обновляем условия
        deal.title = title
        deal.description = description
        deal.price = price
        deal.proposed_by = proposer_id
        deal.proposed_at = timezone.now()
        
        # Сбрасываем согласия и устанавливаем для предложившего
        is_client = str(proposer_id) == str(deal.client_id)
        deal.client_agreed = is_client
        deal.worker_agreed = not is_client
        
        deal.status = 'pending_payment'  # Теперь ждем согласия второй стороны
        deal.save()
        
        # Отправляем карточку в чат
        DealService._send_deal_card(deal, proposer_id, 'proposal', auth_token)
        
        return deal
    
    @staticmethod
    def agree_terms(deal: Deal, user_id: str, auth_token: str):
        """
        Согласиться с предложенными условиями.
        Если обе стороны согласны → можно оплачивать
        """
        if deal.payment_completed:
            raise ValueError("❌ Заказ уже оплачен")
        
        if str(user_id) not in [str(deal.client_id), str(deal.worker_id)]:
            raise ValueError("❌ Вы не участник заказа")
        
        # Нельзя согласиться, если ты сам предложил
        if str(user_id) == str(deal.proposed_by):
            raise ValueError("✅ Вы уже согласны (вы предложили условия)")
        
        # Устанавливаем согласие
        is_client = str(user_id) == str(deal.client_id)
        if is_client:
            deal.client_agreed = True
        else:
            deal.worker_agreed = True
        
        deal.save()
        
        # Если обе стороны согласны → переходим к оплате
        if deal.client_agreed and deal.worker_agreed:
            deal.status = 'pending_payment'
            deal.save()
            DealService._send_deal_card(deal, user_id, 'both_agreed', auth_token)
        else:
            DealService._send_deal_card(deal, user_id, 'agreed', auth_token)
        
        return deal
    
    # ============================================================
    # ЭТАП 2: ОПЛАТА И АКТИВАЦИЯ
    # ============================================================
    
    @staticmethod
    def pay_and_start(deal: Deal, client_id: str, auth_token: str):
        """
        Клиент оплачивает заказ.
        После этого условия ЗАМОРОЖЕНЫ, начинается работа.
        """
        if deal.payment_completed:
            raise ValueError("❌ Заказ уже оплачен")
        
        if str(client_id) != str(deal.client_id):
            raise ValueError("❌ Оплатить может только клиент")
        
        if not (deal.client_agreed and deal.worker_agreed):
            raise ValueError("❌ Обе стороны должны согласиться перед оплатой")
        
        # Создаем транзакцию холдирования
        commission = deal.price * DealService.COMMISSION_RATE
        total = deal.price + commission
        
        transaction = Transaction.objects.create(
            deal=deal,
            amount=total,
            commission=commission,
            status='held',
            payment_provider='stub'
        )
        
        # TODO: Реальное холдирование через платежную систему
        
        # Помечаем как оплаченный и запускаем работу
        deal.payment_completed = True
        deal.payment_completed_at = timezone.now()
        deal.status = 'in_progress'
        deal.history.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'paid',
            'amount': str(total),
        })
        deal.save()
        
        DealService._send_deal_card(deal, client_id, 'paid', auth_token)
        
        return deal
    
    # ============================================================
    # ЭТАП 3: ВЫПОЛНЕНИЕ И СДАЧА РАБОТЫ
    # ============================================================
    
    @staticmethod
    def deliver_work(deal: Deal, worker_id: str, delivery_message: str, auth_token: str):
        """
        Воркер сдает работу на проверку.
        ✅ ИСПРАВЛЕНО: Теперь также отправляет результат в чат как текстовое сообщение
        """
        if str(worker_id) != str(deal.worker_id):
            raise ValueError("❌ Сдать работу может только исполнитель")
        
        if deal.status != 'in_progress':
            raise ValueError(f"❌ Нельзя сдать работу в статусе '{deal.status}'")
        
        deal.status = 'delivered'
        deal.delivered_at = timezone.now()
        deal.delivery_message = delivery_message
        deal.history.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'delivered',
            'message': delivery_message,
        })
        deal.save()
        
        # ✅ Отправляем результат работы в чат как обычное сообщение
        DealService._send_text_message(
            chat_room_id=deal.chat_room_id,
            sender_id=worker_id,
            text=f"📦 **РЕЗУЛЬТАТ РАБОТЫ**\n\n{delivery_message}",
            auth_token=auth_token
        )
        
        # Обновляем карточку заказа
        DealService._send_deal_card(deal, worker_id, 'delivered', auth_token)
        
        return deal
    
    @staticmethod
    def request_revision(deal: Deal, client_id: str, revision_reason: str, auth_token: str):
        """
        Клиент запрашивает доработку (если есть лимит).
        """
        if str(client_id) != str(deal.client_id):
            raise ValueError("❌ Запросить правки может только клиент")
        
        if deal.status != 'delivered':
            raise ValueError("❌ Запросить правки можно только после сдачи работы")
        
        if deal.revision_count >= deal.max_revisions:
            raise ValueError(f"❌ Исчерпан лимит доработок ({deal.max_revisions})")
        
        deal.status = 'in_progress'
        deal.revision_count += 1
        deal.history.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'revision_requested',
            'reason': revision_reason,
            'revision_number': deal.revision_count,
        })
        deal.save()
        
        DealService._send_deal_card(deal, client_id, 'revision_requested', auth_token)
        
        return deal
    
    # ============================================================
    # ЭТАП 4: ЗАВЕРШЕНИЕ
    # ============================================================
    
    @staticmethod
    def complete_deal(deal: Deal, client_id: str, completion_message: str, auth_token: str):
        """
        Клиент принимает работу и завершает заказ.
        Деньги переводятся исполнителю.
        """
        if str(client_id) != str(deal.client_id):
            raise ValueError("❌ Завершить заказ может только клиент")
        
        if deal.status != 'delivered':
            raise ValueError("❌ Завершить можно только сданный заказ")
        
        if not deal.payment_completed:
            raise ValueError("❌ Заказ не был оплачен")
        
        # Переводим деньги исполнителю
        transaction = deal.transactions.filter(status='held').first()
        if transaction:
            transaction.status = 'captured'
            transaction.save()
        
        # TODO: Реальный перевод средств воркеру
        
        deal.status = 'completed'
        deal.completed_at = timezone.now()
        deal.completion_message = completion_message
        deal.history.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'completed',
            'message': completion_message,
        })
        deal.save()
        
        DealService._send_deal_card(deal, client_id, 'completed', auth_token)
        
        return deal
    
    # ============================================================
    # ОТМЕНА
    # ============================================================
    
    @staticmethod
    def cancel_deal(deal: Deal, canceller_id: str, reason: str, auth_token: str):
        """
        Отменить заказ.
        Если был оплачен → возврат средств клиенту.
        """
        if deal.status == 'completed':
            raise ValueError("❌ Нельзя отменить завершенный заказ")
        
        if str(canceller_id) not in [str(deal.client_id), str(deal.worker_id)]:
            raise ValueError("❌ Вы не участник заказа")
        
        was_paid = deal.payment_completed
        
        # Если был оплачен → возвращаем деньги
        if was_paid:
            transaction = deal.transactions.filter(status='held').first()
            if transaction:
                transaction.status = 'refunded'
                transaction.save()
            # TODO: Реальный возврат средств
        
        deal.status = 'cancelled'
        deal.cancelled_by = canceller_id
        deal.cancelled_at = timezone.now()
        deal.cancellation_reason = reason
        deal.history.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'cancelled',
            'by': str(canceller_id),
            'reason': reason,
            'refunded': was_paid,
        })
        deal.save()
        
        DealService._send_deal_card(deal, canceller_id, 'cancelled', auth_token)
        
        return deal
    
    # ============================================================
    # ЗАПРОС ИЗМЕНЕНИЙ (после оплаты)
    # ============================================================
    
    @staticmethod
    def request_change(deal: Deal, requester_id: str, change_reason: str, auth_token: str):
        """
        Запросить изменение условий после оплаты.
        Требует согласия второй стороны + отмена текущего + новый заказ.
        
        Это сложный процесс, лучше просто отменить и создать новый.
        """
        if not deal.payment_completed:
            raise ValueError("❌ До оплаты можно менять условия напрямую")
        
        if str(requester_id) not in [str(deal.client_id), str(deal.worker_id)]:
            raise ValueError("❌ Вы не участник заказа")
        
        deal.change_request_by = requester_id
        deal.change_request_reason = change_reason
        deal.change_request_pending = True
        deal.save()
        
        DealService._send_deal_card(deal, requester_id, 'change_requested', auth_token)
        
        return deal
    
    # ============================================================
    # HELPER: Отправка текстового сообщения в чат
    # ============================================================
    
    @staticmethod
    def _send_text_message(chat_room_id: str, sender_id: str, text: str, auth_token: str):
        """
        ✅ НОВЫЙ метод: Отправляет обычное текстовое сообщение в чат
        """
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
    
    # ============================================================
    # HELPER: Отправка интерактивной карточки в чат
    # ============================================================
    
    @staticmethod
    def _send_deal_card(deal: Deal, sender_id: str, action_type: str, auth_token: str):
        """
        Отправляет или обновляет интерактивную карточку заказа в чате.
        """
        try:
            url = f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/{deal.chat_room_id}/send_deal_message/"
            
            # Данные для карточки
            commission = float(deal.price * DealService.COMMISSION_RATE)
            total = float(deal.price) + commission
            
            deal_data = {
                'deal_id': str(deal.id),
                'title': deal.title,
                'description': deal.description[:200] + '...' if len(deal.description) > 200 else deal.description,
                'price': str(deal.price),
                'commission': f"{commission:.2f}",
                'total': f"{total:.2f}",
                'status': deal.status,
                'client_id': str(deal.client_id),
                'worker_id': str(deal.worker_id),
                'client_agreed': deal.client_agreed,
                'worker_agreed': deal.worker_agreed,
                'payment_completed': deal.payment_completed,
                'revision_count': deal.revision_count,
                'max_revisions': deal.max_revisions,
                'delivery_message': deal.delivery_message or '',
                'can_edit': deal.can_edit_terms(),
                'can_pay': deal.can_pay(),
                'can_deliver': deal.can_deliver(),
                'can_request_revision': deal.can_request_revision(),
                'can_complete': deal.can_complete(),
                'can_cancel': deal.can_cancel(),
            }
            
            # Текст сообщения в зависимости от действия
            message_texts = {
                'proposal': f'📋 Предложение заказа: {deal.title}',
                'agreed': '✅ Условия приняты. Ожидаем второй стороны...',
                'both_agreed': '🎉 Обе стороны согласны! Ожидаем оплату...',
                'paid': f'💳 Заказ оплачен! {total}₽ захолдированы. Можно начинать работу.',
                'delivered': '📦 Работа сдана на проверку',
                'revision_requested': f'🔄 Запрошена доработка ({deal.revision_count}/{deal.max_revisions})',
                'completed': '🎉 Заказ завершен! Деньги переведены исполнителю.',
                'cancelled': '❌ Заказ отменен',
                'change_requested': '⚠️ Запрошено изменение условий после оплаты',
            }
            
            text = message_texts.get(action_type, '📋 Обновление заказа')
            
            payload = {
                'sender_id': str(sender_id),
                'message_type': 'deal_card',
                'text': text,
                'deal_data': deal_data
            }
            
            # Если есть старое сообщение → обновляем
            if deal.last_deal_message_id:
                payload['update_message_id'] = str(deal.last_deal_message_id)
            
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('status') == 'success':
                    message_id = response_data.get('data', {}).get('id')
                    if message_id:
                        deal.last_deal_message_id = message_id
                        deal.save(update_fields=['last_deal_message_id'])
            
        except Exception as e:
            print(f"🔥 Error sending deal card: {e}")
