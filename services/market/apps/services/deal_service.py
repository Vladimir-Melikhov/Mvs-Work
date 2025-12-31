from decimal import Decimal
from django.utils import timezone
from .models import Deal, Transaction, Service
import requests
from django.conf import settings


class DealService:
    """Сервис управления сделками - все операции отправляют интерактивные сообщения в чат"""
    
    COMMISSION_RATE = Decimal('0.08')  # 8%
    
    @staticmethod
    def get_or_create_deal_for_chat(chat_room_id: str, client_id: str, worker_id: str) -> Deal:
        """Получить или создать сделку для чата"""
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
    def propose_deal(deal: Deal, proposer_id: str, title: str, description: str, price: Decimal, auth_token: str):
        """
        Предложить условия сделки.
        Отправляет интерактивную карточку в чат с кнопкой подтверждения.
        """
        if deal.price > 0:
            deal.history.append({
                'timestamp': timezone.now().isoformat(),
                'proposed_by': str(proposer_id),
                'title': deal.title,
                'description': deal.description,
                'price': str(deal.price),
            })
        
        # Обновляем условия
        deal.title = title
        deal.description = description
        deal.price = price
        deal.proposed_by = proposer_id
        deal.proposed_at = timezone.now()
        
        # Определяем роли и правильно устанавливаем подтверждения
        is_client = str(proposer_id) == str(deal.client_id)
        
        # Кто предложил - тот автоматически подтвердил
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
            'client_id': str(deal.client_id),
            'worker_id': str(deal.worker_id),
            'client_confirmed': deal.client_confirmed,
            'worker_confirmed': deal.worker_confirmed,
            'status': 'proposed'
        }
        
        DealService._send_deal_message(
            chat_room_id=deal.chat_room_id,
            sender_id=proposer_id,
            message_type='deal_proposal',
            text='Предложение сделки',
            deal_data=deal_data,
            auth_token=auth_token
        )
        
        return deal
    
    @staticmethod
    def confirm_deal(deal: Deal, confirmer_id: str, auth_token: str):
        """
        Подтвердить сделку.
        Если обе стороны подтвердили → активируем и холдируем деньги.
        """
        is_client = str(confirmer_id) == str(deal.client_id)
        
        if is_client:
            deal.client_confirmed = True
        else:
            deal.worker_confirmed = True
        
        deal.save()
        
        # Если обе подтвердили - активируем
        if deal.client_confirmed and deal.worker_confirmed:
            return DealService._activate_deal(deal, auth_token)
        
        return deal
    
    @staticmethod
    def _activate_deal(deal: Deal, auth_token: str):
        """Активация сделки - холдирование денег и системное сообщение"""
        # Создаем транзакцию (заглушка)
        commission = deal.price * DealService.COMMISSION_RATE
        
        transaction = Transaction.objects.create(
            deal=deal,
            amount=deal.price,
            commission=commission,
            status='held',
            payment_provider='stub'
        )

        deal.status = 'active'
        deal.activated_at = timezone.now()
        deal.save()

        deal_data = {
            'deal_id': str(deal.id),
            'title': deal.title,
            'price': str(deal.price),
            'status': 'active',
            'activated_at': deal.activated_at.isoformat()
        }
        
        DealService._send_deal_message(
            chat_room_id=deal.chat_room_id,
            sender_id=deal.client_id,
            message_type='deal_activated',
            text='Сделка активирована',
            deal_data=deal_data,
            auth_token=auth_token
        )
        
        return deal
    
    @staticmethod
    def request_completion(deal: Deal, requester_id: str, auth_token: str):
        """Запрос на завершение - отправляет карточку в чат"""
        if deal.status != 'active':
            raise ValueError("Сделка не активна")
        
        is_client = str(requester_id) == str(deal.client_id)
        
        deal_data = {
            'deal_id': str(deal.id),
            'title': deal.title,
            'price': str(deal.price),
            'requester_id': str(requester_id),
            'requester_role': 'client' if is_client else 'worker',
            'status': 'completion_requested'
        }
        
        DealService._send_deal_message(
            chat_room_id=deal.chat_room_id,
            sender_id=requester_id,
            message_type='deal_completion_request',
            text='Запрос на завершение сделки',
            deal_data=deal_data,
            auth_token=auth_token
        )
        
        return deal
    
    @staticmethod
    def complete_deal(deal: Deal, completer_id: str, auth_token: str):
        """Завершить сделку - перевод денег исполнителю"""
        if deal.status != 'active':
            raise ValueError("Сделка не активна")
        
        # Находим транзакцию и завершаем
        transaction = deal.transactions.filter(status='held').first()
        if not transaction:
            raise ValueError("Транзакция не найдена")
        
        transaction.status = 'captured'
        transaction.save()
        
        deal.status = 'completed'
        deal.completed_at = timezone.now()
        deal.save()
        
        # TODO: Реальное пополнение баланса воркера
        
        # Отправляем карточку завершения
        deal_data = {
            'deal_id': str(deal.id),
            'title': deal.title,
            'price': str(deal.price),
            'status': 'completed',
            'completed_at': deal.completed_at.isoformat()
        }
        
        DealService._send_deal_message(
            chat_room_id=deal.chat_room_id,
            sender_id=completer_id,
            message_type='deal_completed',
            text='Сделка завершена',
            deal_data=deal_data,
            auth_token=auth_token
        )
        
        return deal
    
    @staticmethod
    def cancel_deal(deal: Deal, canceller_id: str, reason: str, auth_token: str):
        """Отменить сделку - возврат денег"""
        if deal.status == 'completed':
            raise ValueError("Нельзя отменить завершенную сделку")
        
        # Возвращаем деньги если была активна
        if deal.status == 'active':
            transaction = deal.transactions.filter(status='held').first()
            if transaction:
                transaction.status = 'refunded'
                transaction.save()
        
        old_status = deal.status
        deal.status = 'cancelled'
        deal.save()
        
        is_client = str(canceller_id) == str(deal.client_id)
        
        deal_data = {
            'deal_id': str(deal.id),
            'title': deal.title,
            'price': str(deal.price),
            'canceller_role': 'client' if is_client else 'worker',
            'reason': reason,
            'was_active': old_status == 'active',
            'status': 'cancelled'
        }
        
        DealService._send_deal_message(
            chat_room_id=deal.chat_room_id,
            sender_id=canceller_id,
            message_type='deal_cancelled',
            text='Сделка отменена',
            deal_data=deal_data,
            auth_token=auth_token
        )

        return deal

    @staticmethod
    def _send_deal_message(chat_room_id: str, sender_id: str, message_type: str, text: str, deal_data: dict, auth_token: str):
        """Отправить интерактивное сообщение о сделке в чат"""
        try:
            url = f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/{chat_room_id}/send_deal_message/"
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                url,
                headers=headers,
                json={
                    'sender_id': str(sender_id),
                    'message_type': message_type,
                    'text': text,
                    'deal_data': deal_data
                },
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Failed to send deal message: {response.text}")
                
        except Exception as e:
            print(f"Error sending deal message: {e}")
