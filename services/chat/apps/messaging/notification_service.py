# services/chat/apps/messaging/notification_service.py
"""
Централизованный сервис для отправки Telegram уведомлений.
Обрабатывает все типы сообщений: текстовые, системные, карточки сделок.
"""
import os
import requests
from typing import Optional, Dict
from .auth_client import AuthServiceClient


class TelegramNotificationService:
    """Сервис отправки уведомлений в Telegram"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.auth_client = AuthServiceClient()
    
    def send_notification(
        self, 
        message, 
        sender_id: str, 
        room_members: list
    ) -> bool:
        """
        Отправить уведомление о новом сообщении
        
        Args:
            message: объект Message из БД
            sender_id: ID отправителя
            room_members: список ID участников комнаты
        
        Returns:
            bool: успешность отправки
        """
        if not self.bot_token:
            print("[TELEGRAM] ❌ Bot token не настроен")
            return False
        
        # Находим получателя
        receiver_id = self._get_receiver_id(sender_id, room_members)
        if not receiver_id:
            print("[TELEGRAM] ❌ Получатель не найден")
            return False
        
        # Получаем данные получателя
        receiver_data = self.auth_client.get_user_profile(receiver_id)
        if not receiver_data:
            print(f"[TELEGRAM] ❌ Профиль получателя {receiver_id} не найден")
            return False
        
        # Проверяем настройки уведомлений
        profile = receiver_data.get('profile', {})
        telegram_chat_id = profile.get('telegram_chat_id')
        telegram_enabled = profile.get('telegram_notifications_enabled', False)
        
        if not telegram_chat_id or not telegram_enabled:
            print(f"[TELEGRAM] ℹ️ Уведомления отключены для пользователя {receiver_id}")
            return False
        
        # Получаем имя отправителя
        sender_name = self._get_sender_name(sender_id)
        
        # Формируем текст уведомления в зависимости от типа сообщения
        notification_text = self._format_notification(message, sender_name)
        
        # Отправляем через Telegram API
        return self._send_to_telegram(telegram_chat_id, notification_text)
    
    def _get_receiver_id(self, sender_id: str, members: list) -> Optional[str]:
        """Найти ID получателя (не отправителя)"""
        for member_id in members:
            if str(member_id) != str(sender_id):
                return str(member_id)
        return None
    
    def _get_sender_name(self, sender_id: str) -> str:
        """Получить имя отправителя"""
        sender_data = self.auth_client.get_user_profile(sender_id)
        
        if not sender_data:
            return "Пользователь"
        
        sender_profile = sender_data.get('profile', {})
        return (
            sender_profile.get('full_name') or 
            sender_profile.get('company_name') or 
            sender_data.get('email', 'Пользователь')
        )
    
    def _format_notification(self, message, sender_name: str) -> str:
        """
        Форматировать текст уведомления в зависимости от типа сообщения
        """
        message_type = message.message_type
        text = message.text or ''
        
        # Обычное текстовое сообщение
        if message_type == 'text':
            text_preview = text[:100] + ('...' if len(text) > 100 else '')
            return f"💬 <b>Новое сообщение от {sender_name}</b>\n\n{text_preview}"
        
        # Системное сообщение о сделке
        if message_type in ['system', 'deal_card']:
            # Извлекаем эмодзи и первую строку для краткого уведомления
            first_line = text.split('\n')[0] if text else 'Обновление заказа'
            return f"🔔 <b>{sender_name}</b>\n\n{first_line}"
        
        # Другие типы сообщений
        return f"🔔 <b>Уведомление от {sender_name}</b>\n\n{text[:100]}"
    
    def _send_to_telegram(self, chat_id: int, text: str) -> bool:
        """Отправить сообщение через Telegram Bot API"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            response = requests.post(
                url,
                json={
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': 'HTML'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[TELEGRAM] ✅ Уведомление отправлено в чат {chat_id}")
                return True
            else:
                print(f"[TELEGRAM] ❌ Ошибка API: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[TELEGRAM] ⚠️ Исключение при отправке: {e}")
            return False