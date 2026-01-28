import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:8001')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start"""
    
    # Проверяем наличие deep link токена
    if context.args and len(context.args) > 0:
        token = context.args[0]
        chat_id = update.effective_chat.id
        username = update.effective_user.username or "Unknown"
        
        # Верифицируем токен через Auth Service
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/api/auth/telegram/verify-token/",
                json={
                    'token': token,
                    'telegram_chat_id': chat_id,
                    'telegram_username': username
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                await update.message.reply_text(
                    f"✅ Отлично! Уведомления активированы.\n\n"
                    f"Теперь вы будете получать уведомления о новых сообщениях в этот чат."
                )
            else:
                error = response.json().get('error', 'Неизвестная ошибка')
                await update.message.reply_text(
                    f"❌ Ошибка активации: {error}\n\n"
                    f"Попробуйте сгенерировать новую ссылку в настройках."
                )
                
        except Exception as e:
            logger.error(f"Ошибка верификации токена: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при активации уведомлений.\n"
                "Попробуйте еще раз или обратитесь в поддержку."
            )
    else:
        # Обычный /start без токена
        await update.message.reply_text(
            "👋 Привет! Это бот уведомлений Mvs-Work.\n\n"
            "Для активации уведомлений:\n"
            "1. Откройте настройки чата в веб-приложении\n"
            "2. Нажмите 'Подключить Telegram уведомления'\n"
            "3. Перейдите по ссылке\n\n"
            "После этого вы будете получать уведомления о новых сообщениях."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /help"""
    await update.message.reply_text(
        "📖 <b>Помощь по боту Mvs-Work</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/status - Проверить статус уведомлений\n\n"
        "<b>Как это работает:</b>\n"
        "• Подключите уведомления через веб-приложение\n"
        "• Получайте мгновенные уведомления о новых сообщениях\n"
        "• Управляйте настройками в профиле",
        parse_mode='HTML'
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса уведомлений"""
    chat_id = update.effective_chat.id
    
    try:
        # Проверяем, привязан ли этот chat_id к аккаунту
        response = requests.post(
            f"{AUTH_SERVICE_URL}/api/auth/telegram/get-user/",
            json={'telegram_chat_id': chat_id},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            email = data.get('email', 'Unknown')
            await update.message.reply_text(
                f"✅ <b>Уведомления активны</b>\n\n"
                f"Аккаунт: {email}\n"
                f"Telegram ID: {chat_id}\n\n"
                f"Вы получаете уведомления о новых сообщениях.",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ <b>Уведомления не активированы</b>\n\n"
                "Для активации:\n"
                "1. Откройте настройки чата в веб-приложении\n"
                "2. Нажмите 'Подключить Telegram уведомления'\n"
                "3. Перейдите по ссылке",
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        await update.message.reply_text(
            "⚠️ Не удалось проверить статус уведомлений.\n"
            "Попробуйте позже."
        )


def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в переменных окружения!")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Запускаем бота
    logger.info("🤖 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
