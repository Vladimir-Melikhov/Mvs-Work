from decimal import Decimal
from django.utils import timezone
from .models import Deal, Transaction, Service
import requests
from django.conf import settings


class DealService:
    """
    Сервис управления сделками - строгая бизнес-логика
    
    ЖИЗНЕННЫЙ ЦИКЛ СДЕЛКИ:
    1. draft → Сделка создана, но еще не предложена
    2. proposed → Одна сторона предложила условия, ждем второй стороны
    3. active → Обе подтвердили, деньги захолдированы
    4. completion_requested → Одна сторона запросила завершение
    5. completed → Обе подтвердили завершение, деньги переведены
    6. cancelled → Сделка отменена
    """
    
    COMMISSION_RATE = Decimal('0.08')  # 8%
    
    @staticmethod
    def get_or_create_deal_for_chat(chat_room_id: str, client_id: str, worker_id: str) -> Deal:
        """
        Получить или создать сделку для чата.
        Роли определяются ОДИН РАЗ при создании и НЕ МЕНЯЮТСЯ.
        """
        deal, created = Deal.objects.get_or_create(
            chat_room_id=chat_room_id,
            defaults={
                'client_id': client_id,
                'worker_id': worker_id,
                'title': 'Новая сделка',
                'description': 'Условия обсуждаются',
                'price': Decimal('0.00'),
                'status': 'draft'
            }
        )
        return deal
    
    @staticmethod
    def can_propose(deal: Deal, proposer_id: str) -> tuple[bool, str]:
        """Проверка: можно ли предложить условия"""
        # Нельзя редактировать активные/завершенные сделки
        if deal.status in ['active', 'completion_requested', 'completed']:
            return False, f"Сделка в статусе '{deal.status}' не может быть изменена"
        
        # Нельзя редактировать отмененную сделку
        if deal.status == 'cancelled':
            return False, "Отмененную сделку нельзя редактировать"
        
        # Только участники сделки могут предлагать условия
        if str(proposer_id) not in [str(deal.client_id), str(deal.worker_id)]:
            return False, "Вы не являетесь участником этой сделки"
        
        return True, "OK"
    
    @staticmethod
    def propose_deal(deal: Deal, proposer_id: str, title: str, description: str, price: Decimal, auth_token: str):
        """
        Предложить условия сделки.
        
        ПРАВИЛА:
        - Можно редактировать только в статусе draft/proposed
        - Кто предложил - автоматически подтвердил
        - Вторая сторона должна подтвердить
        - ✅ ОБНОВЛЯЕТ старую карточку вместо создания новой
        """
        # Валидация
        can_propose, error = DealService.can_propose(deal, proposer_id)
        if not can_propose:
            raise ValueError(error)
        
        # Сохраняем старую версию в историю (если была)
        if deal.price > 0:
            deal.history.append({
                'timestamp': timezone.now().isoformat(),
                'proposed_by': str(deal.proposed_by) if deal.proposed_by else None,
                'title': deal.title,
                'description': deal.description,
                'price': str(deal.price),
                'status': deal.status
            })
        
        # Обновляем условия
        deal.title = title
        deal.description = description
        deal.price = price
        deal.proposed_by = proposer_id
        deal.proposed_at = timezone.now()
        
        # Сбрасываем подтверждения и устанавливаем для предложившего
        is_client = str(proposer_id) == str(deal.client_id)
        
        if is_client:
            deal.client_confirmed = True
            deal.worker_confirmed = False
        else:
            deal.worker_confirmed = True
            deal.client_confirmed = False
        
        deal.status = 'proposed'
        deal.save()
        
        # Отправляем интерактивную карточку в чат
        commission = float(price) * 0.08
        total = float(price) + commission
        
        deal_data = {
            'deal_id': str(deal.id),
            'title': title,
            'description': description,
            'price': str(price),
            'commission': f"{commission:.2f}",
            'total': f"{total:.2f}",
            'proposer_id': str(proposer_id),
            'proposer_role': 'client' if is_client else 'worker',
            'client_id': str(deal.client_id),
            'worker_id': str(deal.worker_id),
            'client_confirmed': deal.client_confirmed,
            'worker_confirmed': deal.worker_confirmed,
            'status': 'proposed'
        }
        
        # ✅ ОБНОВЛЯЕМ или создаем карточку
        message_id = DealService._send_or_update_deal_message(
            deal=deal,
            sender_id=proposer_id,
            message_type='deal_proposal',
            text=f'💼 Новое предложение сделки: {title}',
            deal_data=deal_data,
            auth_token=auth_token
        )
        
        # Сохраняем ID сообщения
        if message_id:
            deal.last_deal_message_id = message_id
            deal.save(update_fields=['last_deal_message_id'])
        
        return deal
    
    @staticmethod
    def can_confirm(deal: Deal, confirmer_id: str) -> tuple[bool, str]:
        """Проверка: можно ли подтвердить сделку"""
        # Подтверждать можно только предложенную сделку
        if deal.status != 'proposed':
            return False, f"Сделка не в статусе 'proposed' (текущий: {deal.status})"
        
        # Только участники могут подтверждать
        if str(confirmer_id) not in [str(deal.client_id), str(deal.worker_id)]:
            return False, "Вы не являетесь участником этой сделки"
        
        # Нельзя подтверждать, если ты сам предложил
        if str(confirmer_id) == str(deal.proposed_by):
            return False, "Вы уже подтвердили условия (вы их предложили)"
        
        # Проверяем, не подтверждено ли уже
        is_client = str(confirmer_id) == str(deal.client_id)
        already_confirmed = deal.client_confirmed if is_client else deal.worker_confirmed
        
        if already_confirmed:
            return False, "Вы уже подтвердили эту сделку"
        
        return True, "OK"
    
    @staticmethod
    def confirm_deal(deal: Deal, confirmer_id: str, auth_token: str):
        """
        Подтвердить сделку.
        Если обе стороны подтвердили → активируем и холдируем деньги.
        ✅ ОБНОВЛЯЕТ карточку вместо создания новой
        """
        # Валидация
        can_confirm, error = DealService.can_confirm(deal, confirmer_id)
        if not can_confirm:
            raise ValueError(error)
        
        # Подтверждаем от имени подтверждающего
        is_client = str(confirmer_id) == str(deal.client_id)
        
        if is_client:
            deal.client_confirmed = True
        else:
            deal.worker_confirmed = True
        
        deal.save()
        
        # Если обе стороны подтвердили - активируем
        if deal.client_confirmed and deal.worker_confirmed:
            return DealService._activate_deal(deal, auth_token)
        else:
            # ✅ ОБНОВЛЯЕМ карточку с новым статусом подтверждений
            deal_data = {
                'deal_id': str(deal.id),
                'title': deal.title,
                'description': deal.description,
                'price': str(deal.price),
                'commission': f"{float(deal.price) * 0.08:.2f}",
                'total': f"{float(deal.price) * 1.08:.2f}",
                'proposer_id': str(deal.proposed_by),
                'client_id': str(deal.client_id),
                'worker_id': str(deal.worker_id),
                'client_confirmed': deal.client_confirmed,
                'worker_confirmed': deal.worker_confirmed,
                'status': 'proposed'
            }
            
            message_id = DealService._send_or_update_deal_message(
                deal=deal,
                sender_id=confirmer_id,
                message_type='deal_proposal',
                text='✅ Условия подтверждены. Ожидаем второй стороны...',
                deal_data=deal_data,
                auth_token=auth_token
            )
            
            if message_id:
                deal.last_deal_message_id = message_id
                deal.save(update_fields=['last_deal_message_id'])
        
        return deal
    
    @staticmethod
    def _activate_deal(deal: Deal, auth_token: str):
        """
        Активация сделки - холдирование денег и системное сообщение
        ✅ ОБНОВЛЯЕТ карточку
        """
        # TODO: Реальная проверка баланса клиента через Auth Service
        
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
        
        # TODO: Реальное холдирование через Auth Service

        deal.status = 'active'
        deal.activated_at = timezone.now()
        deal.save()

        deal_data = {
            'deal_id': str(deal.id),
            'title': deal.title,
            'price': str(deal.price),
            'commission': str(commission),
            'total': str(total),
            'status': 'active',
            'activated_at': deal.activated_at.isoformat()
        }
        
        # ✅ ОБНОВЛЯЕМ карточку
        message_id = DealService._send_or_update_deal_message(
            deal=deal,
            sender_id=deal.client_id,
            message_type='deal_activated',
            text=f'🎉 Сделка активирована! {total}₽ захолдированы.',
            deal_data=deal_data,
            auth_token=auth_token
        )
        
        if message_id:
            deal.last_deal_message_id = message_id
            deal.save(update_fields=['last_deal_message_id'])
        
        return deal
    
    @staticmethod
    def can_request_completion(deal: Deal, requester_id: str) -> tuple[bool, str]:
        """Проверка: можно ли запросить завершение"""
        if deal.status != 'active':
            return False, f"Сделка не активна (текущий статус: {deal.status})"
        
        if str(requester_id) not in [str(deal.client_id), str(deal.worker_id)]:
            return False, "Вы не являетесь участником этой сделки"
        
        return True, "OK"
    
    @staticmethod
    def request_completion(deal: Deal, requester_id: str, auth_token: str):
        """
        Запрос на завершение
        ✅ ОБНОВЛЯЕТ карточку
        """
        can_request, error = DealService.can_request_completion(deal, requester_id)
        if not can_request:
            raise ValueError(error)
        
        # Сохраняем информацию о запросе
        deal.status = 'completion_requested'
        deal.completion_requested_by = requester_id
        deal.completion_requested_at = timezone.now()
        deal.save()
        
        is_client = str(requester_id) == str(deal.client_id)
        
        deal_data = {
            'deal_id': str(deal.id),
            'title': deal.title,
            'price': str(deal.price),
            'requester_id': str(requester_id),
            'requester_role': 'client' if is_client else 'worker',
            'status': 'completion_requested'
        }
        
        # ✅ ОБНОВЛЯЕМ карточку
        message_id = DealService._send_or_update_deal_message(
            deal=deal,
            sender_id=requester_id,
            message_type='deal_completion_request',
            text='🎯 Запрос на завершение сделки',
            deal_data=deal_data,
            auth_token=auth_token
        )
        
        if message_id:
            deal.last_deal_message_id = message_id
            deal.save(update_fields=['last_deal_message_id'])
        
        return deal
    
    @staticmethod
    def can_complete(deal: Deal, completer_id: str) -> tuple[bool, str]:
        """Проверка: можно ли завершить сделку"""
        if deal.status != 'completion_requested':
            return False, f"Нет запроса на завершение (текущий статус: {deal.status})"
        
        if str(completer_id) not in [str(deal.client_id), str(deal.worker_id)]:
            return False, "Вы не являетесь участником этой сделки"
        
        if str(completer_id) == str(deal.completion_requested_by):
            return False, "Вы уже запросили завершение. Ждем подтверждения второй стороны."
        
        return True, "OK"
    
    @staticmethod
    def complete_deal(deal: Deal, completer_id: str, auth_token: str):
        """
        Завершить сделку
        ✅ ОБНОВЛЯЕТ карточку
        """
        can_complete, error = DealService.can_complete(deal, completer_id)
        if not can_complete:
            raise ValueError(error)
        
        transaction = deal.transactions.filter(status='held').first()
        if not transaction:
            raise ValueError("Транзакция не найдена")
        
        transaction.status = 'captured'
        transaction.save()
        
        deal.status = 'completed'
        deal.completed_at = timezone.now()
        deal.save()
        
        # TODO: Реальное пополнение баланса воркера
        
        deal_data = {
            'deal_id': str(deal.id),
            'title': deal.title,
            'price': str(deal.price),
            'status': 'completed',
            'completed_at': deal.completed_at.isoformat()
        }
        
        # ✅ ОБНОВЛЯЕМ карточку
        message_id = DealService._send_or_update_deal_message(
            deal=deal,
            sender_id=completer_id,
            message_type='deal_completed',
            text=f'🎉 Сделка завершена! {deal.price}₽ переведены исполнителю.',
            deal_data=deal_data,
            auth_token=auth_token
        )
        
        if message_id:
            deal.last_deal_message_id = message_id
            deal.save(update_fields=['last_deal_message_id'])
        
        return deal
    
    @staticmethod
    def can_cancel(deal: Deal, canceller_id: str) -> tuple[bool, str]:
        """Проверка: можно ли отменить сделку"""
        if deal.status == 'completed':
            return False, "Нельзя отменить завершенную сделку"
        
        if str(canceller_id) not in [str(deal.client_id), str(deal.worker_id)]:
            return False, "Вы не являетесь участником этой сделки"
        
        return True, "OK"
    
    @staticmethod
    def cancel_deal(deal: Deal, canceller_id: str, reason: str, auth_token: str):
        """
        Отменить сделку
        ✅ ОБНОВЛЯЕТ карточку
        """
        can_cancel, error = DealService.can_cancel(deal, canceller_id)
        if not can_cancel:
            raise ValueError(error)
        
        was_active = deal.status in ['active', 'completion_requested']
        
        if was_active:
            transaction = deal.transactions.filter(status='held').first()
            if transaction:
                transaction.status = 'refunded'
                transaction.save()
                # TODO: Реальный возврат средств
        
        deal.status = 'cancelled'
        deal.cancelled_by = canceller_id
        deal.cancellation_reason = reason
        deal.save()
        
        is_client = str(canceller_id) == str(deal.client_id)
        
        deal_data = {
            'deal_id': str(deal.id),
            'title': deal.title,
            'price': str(deal.price),
            'canceller_id': str(canceller_id),
            'canceller_role': 'client' if is_client else 'worker',
            'reason': reason,
            'was_active': was_active,
            'status': 'cancelled'
        }
        
        refund_text = f" Средства возвращены клиенту." if was_active else ""
        
        # ✅ ОБНОВЛЯЕМ карточку
        message_id = DealService._send_or_update_deal_message(
            deal=deal,
            sender_id=canceller_id,
            message_type='deal_cancelled',
            text=f'❌ Сделка отменена.{refund_text}',
            deal_data=deal_data,
            auth_token=auth_token
        )
        
        if message_id:
            deal.last_deal_message_id = message_id
            deal.save(update_fields=['last_deal_message_id'])

        return deal

    @staticmethod
    def _send_or_update_deal_message(deal: Deal, sender_id: str, message_type: str, text: str, deal_data: dict, auth_token: str):
        """
        ✅ ОБНОВЛЯЕТ существующую карточку или создает новую
        
        Если у сделки есть last_deal_message_id - обновляем старое сообщение
        Иначе - создаем новое
        
        Returns: message_id (str) или None
        """
        try:
            url = f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/{deal.chat_room_id}/send_deal_message/"
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'sender_id': str(sender_id),
                'message_type': message_type,
                'text': text,
                'deal_data': deal_data
            }
            
            # ✅ Если есть старое сообщение - обновляем его
            if deal.last_deal_message_id:
                payload['update_message_id'] = str(deal.last_deal_message_id)
            
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('status') == 'success':
                    return response_data.get('data', {}).get('id')
            else:
                print(f"⚠️ Failed to send deal message: {response.text}")
                return None
                
        except Exception as e:
            print(f"🔥 Error sending deal message: {e}")
            return None
