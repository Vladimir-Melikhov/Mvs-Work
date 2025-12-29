import os
import requests
import json
from django.conf import settings
from .models import Service
# Order больше не импортируем, так как модели нет

class AIService:
    """
    AI-сервис для генерации СТРОГОГО ТЗ через io.net (DeepSeek-R1).
    Убирает галлюцинации и лишние теги <think>.
    """
    
    @staticmethod
    def generate_tz(service_id: str, client_requirements: str) -> str:
        try:
            service = Service.objects.get(id=service_id)
            api_key = os.getenv('IO_NET_API_KEY')
            
            # URL API io.net (serverless)
            base_url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
            
            # Если ключа нет — возвращаем заглушку
            if not api_key:
                print("⚠️ [Market] Нет IO_NET_API_KEY")
                return AIService._generate_mock_tz(client_requirements, service.price, service.title)

            # --- СТРОГИЙ СИСТЕМНЫЙ ПРОМПТ ---
            system_instruction = """Ты — строгий технический документатор.
Твоя задача — составить ТЗ, объединив "Требования исполнителя" (Бриф) и "Ответы заказчика".

ГЛАВНЫЕ ПРАВИЛА (СОБЛЮДАТЬ СТРОГО):
1. ЗАПРЕЩЕНО выдумывать технические детали (библиотеки, фреймворки), если их нет в тексте.
2. ЗАПРЕЩЕНО выдумывать дизайн-решения (шрифты, цвета), если они не указаны явно.
3. Если заказчик пишет "простой сайт", НЕ пиши про сложные анимации или API, если этого не просили.
4. Если информации не хватает (например, клиент не ответил на вопрос из брифа) — добавляй пункт в раздел "Вопросы для уточнения".

Формат вывода (Markdown):
# ТЗ: [Название услуги]
## 1. Задача (Суть своими словами)
## 2. Стек и Условия (Строго то, что указал исполнитель)
## 3. Функционал (То, что попросил заказчик)
## 4. Дизайн и Контент (Реальные пожелания: цвета, референсы)
## 5. Вопросы и Уточнения (Чего не хватает для работы)"""

            # Требования фрилансера (Бриф)
            freelancer_reqs = service.ai_template if service.ai_template else "Исполнитель не указал жестких требований."
            
            user_content = f"""
ДАННЫЕ ДЛЯ ТЗ:

1. ИСПОЛНИТЕЛЬ (БРИФ / ТРЕБОВАНИЯ):
Услуга: {service.title}
Условия: "{freelancer_reqs}"

2. ЗАКАЗЧИК (ОТВЕТЫ / ПОЖЕЛАНИЯ):
Запрос: "{client_requirements}"

Сгенерируй ТЗ, используя ТОЛЬКО эти данные. Не добавляй "воду"."""

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": "deepseek-ai/DeepSeek-R1-0528", 
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.3, # Низкая температура для отсутствия фантазий
                "max_tokens": 8000
            }

            print(f"🔄 [Market] Генерация ТЗ (DeepSeek-R1)...")
            
            response = requests.post(base_url, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 200:
                data = response.json()
                try:
                    raw_content = data['choices'][0]['message']['content']
                    
                    # --- ОЧИСТКА ОТ <think> ---
                    # DeepSeek-R1 пишет свои мысли в тегах <think>...</think>. Нам они в ТЗ не нужны.
                    if "</think>" in raw_content:
                        final_tz = raw_content.split("</think>")[-1].strip()
                    else:
                        final_tz = raw_content

                    return final_tz
                    
                except Exception:
                    return AIService._generate_mock_tz(client_requirements, service.price, service.title)
            else:
                print(f"⚠️ Ошибка API ({response.status_code}): {response.text}")
                return AIService._generate_mock_tz(client_requirements, service.price, service.title)

        except Exception as e:
            print(f"🔥 Ошибка сервиса AI: {e}")
            return AIService._generate_mock_tz(client_requirements, 0, "Проект")

    @staticmethod
    def _generate_mock_tz(requirements: str, price: float, title: str) -> str:
        """Заглушка, если нейросеть недоступна"""
        return f"# ТЗ: {title}\n\n## Задача\n{requirements}\n\n## Бюджет\n${price}\n\n_Примечание: AI временно недоступен, это автоматический черновик._"
    