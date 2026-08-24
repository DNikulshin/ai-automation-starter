import logging
from pathlib import Path
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        self.enabled = enabled and bool(bot_token and chat_id)
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.chat_id = chat_id

    def send(self, message: str, parse_mode: str = "Markdown") -> bool:
        if not self.enabled:
            return False
        try:
            resp = requests.post(
                self.url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                },
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Telegram notification failed: {e}")
            return False

    def notify_startup(self, unprocessed_count: int) -> None:
        if unprocessed_count == 0:
            self.send("🟢 *Пайплайн готов*. Очередь пуста.")
        else:
            self.send(
                f"🚀 *Запуск пайплайна*\nВ обработке: `{unprocessed_count}` файлов"
            )

    def notify_success(self, filename: str, data: Dict[str, Any]) -> None:
        patient = data.get("patient_name") or data.get("summary", "Неизвестный")
        date = data.get("date", "—")
        msg = (
            f"✅ *Приём обработан*\n"
            f"👤 {patient}\n"
            f"📅 Дата: {date}\n"
            f"📄 Исходник: `{filename}`\n"
            f"📁 Карта сохранена в базу знаний"
        )
        self.send(msg)

    def notify_error(self, filename: str, error: str) -> None:
        # Обрезаем и чистим текст ошибки для читаемости
        clean_error = error.split("\n")[0][:150]
        msg = (
            f"❌ *Ошибка обработки*\n"
            f"📄 `{filename}`\n"
            f"⚠️ `{clean_error}`\n"
            f"💡 Проверьте формат файла или повторите попытку позже"
        )
        self.send(msg)

    def notify_daily_summary(self, success: int, failed: int) -> None:
        if success == 0 and failed == 0:
            return
        msg = (
            f"📊 *Итоги за день*\n"
            f"✅ Успешно: `{success}`\n"
            f"❌ Ошибки: `{failed}`"
        )
        self.send(msg)
