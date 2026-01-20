import os
import requests
from django.conf import settings
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


class OrderService:
    """Бизнес-логика работы с заказами"""

    @staticmethod
    def create_order(service_id: str, client_id: str, agreed_tz: str, auth_token: str):
        try:
            service = Service.objects.get(id=service_id)
            order = Deal.objects.create(
                service=service, 
                client_id=client_id, 
                worker_id=service.owner_id,
                description=agreed_tz,
                price=service.price, 
                status='pending'
            )
            try:
                chat_url = f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/"
                headers = {'Authorization': f'Bearer {auth_token}', 'Content-Type': 'application/json'}
                resp = requests.post(chat_url, headers=headers, json={'member_ids': [str(client_id), str(service.owner_id)]}, timeout=5)

                if resp.status_code == 201:
                    room_id = resp.json()['data']['id']
                    tz_msg = f"📋 НОВЫЙ ЗАКАЗ\n\n{agreed_tz}"
                    if len(agreed_tz) > 2000:
                        tz_msg = f"📋 НОВЫЙ ЗАКАЗ\n\n{agreed_tz[:1500]}...\n\n_(Полное ТЗ доступно в деталях заказа)_"

                    requests.post(
                        f"{settings.CHAT_SERVICE_URL}/api/chat/rooms/{room_id}/send_message/",
                        headers=headers,
                        json={'sender_id': str(client_id), 'text': tz_msg, 'is_system': False},
                        timeout=5
                    )
            except Exception as e:
                print(f"Chat error: {e}")
            return order
        except Service.DoesNotExist:
            raise ValueError("Service not found")
