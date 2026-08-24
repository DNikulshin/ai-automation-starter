#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к OpenRouter API.
Загружает конфигурацию из .env, отправляет тестовый запрос и выводит ответ.
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Загружаем переменные из .env в корне проекта
# project_root = Path(__file__).parent.parent  # если скрипт в tests/
project_root = Path(__file__).parent
env_path = project_root / ".env"

if not env_path.exists():
    print(f"⚠️  Файл .env не найден по пути: {env_path}", file=sys.stderr)
    print("💡 Создайте .env на основе .env.example", file=sys.stderr)
    sys.exit(1)

load_dotenv(env_path)

# === Конфигурация из окружения ===
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("LLM_MODEL", "google/gemma-4-31b-it:free")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Обязательные хедеры для OpenRouter (особенно для free-моделей)
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": os.getenv("HTTP_REFERER", "https://github.com/DNikulshin"),
    "X-Title": os.getenv("APP_TITLE", "ai-automation-starter"),
}

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def test_connection() -> bool:
    """Проверяет валидность ключа через /auth/key"""
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            print(
                f"✅ Ключ валиден. Провайдер: {data.get('data', {}).get('provider_name', 'N/A')}"
            )
            return True
        else:
            print(f"❌ Ошибка авторизации: {resp.status_code} — {resp.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Ошибка сети при проверке ключа: {e}")
        return False


def test_llm_completion(prompt: str) -> dict | None:
    """Отправляет запрос к LLM с повторными попытками"""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.3,
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                ENDPOINT,
                headers=HEADERS,
                json=payload,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            last_error = e
            print(f"⚠️ Попытка {attempt}/{MAX_RETRIES} не удалась: {e}")
            if attempt < MAX_RETRIES:
                import time

                time.sleep(2**attempt)  # экспоненциальная задержка

    print(f"❌ Все {MAX_RETRIES} попыток исчерпаны. Последняя ошибка: {last_error}")
    return None


def main():
    # Настройка UTF-8 вывода для Windows/PowerShell
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

    print(f"🔍 Тест подключения к OpenRouter (модель: {MODEL})")
    print("-" * 60)

    # 1. Проверка ключа
    if not API_KEY:
        print("❌ OPENROUTER_API_KEY не задан в .env")
        sys.exit(1)

    if not test_connection():
        sys.exit(2)

    # 2. Тестовый запрос
    test_prompts = [
        "Ответь одним предложением на русском: зачем нужна автоматизация?",
        "Извлеки из текста дату и задачу: 'Встреча с пациентом 15 мая, нужно подготовить историю болезни.'",
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Запрос #{i}: {prompt}")
        result = test_llm_completion(prompt)

        if result and "choices" in result:
            content = result["choices"][0]["message"]["content"]
            print(f"✅ Ответ:\n{content.strip()}")

            # Сохраняем в файл для отладки (опционально)
            debug_file = Path("test_output.json")
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 Полный ответ сохранён в {debug_file}")
        else:
            print("❌ Не удалось получить ответ")

    print("\n" + "=" * 60)
    print("✨ Тест завершён")


if __name__ == "__main__":
    main()
