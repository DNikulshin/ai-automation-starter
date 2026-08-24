import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import yaml
from pydantic import ValidationError

from src.config import AppConfig
from src.models import ProcessedData

# Настройка структурированного логгера
logger = logging.getLogger(__name__)


class LLMProcessor:
    def __init__(self, config: AppConfig, prompt_path: Path | None = None):
        self.config = config
        self.prompt = self._load_prompt(prompt_path or Path("prompts/default.yaml"))

    def _load_prompt(self, path: Path) -> Dict[str, str]:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _call_llm(self, text: str, attempt: int) -> str:
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.config.http_referer or "https://github.com/DNikulshin",
            "X-Title": self.config.app_title or "ai-automation-starter",
        }
        payload = {
            "model": self.config.llm_model,
            "messages": [
                {"role": "system", "content": self.prompt["system"]},
                {"role": "user", "content": self.prompt["template"].format(text=text)},
            ],
        }

        logger.info(
            "llm_request",
            extra={
                "event": "llm_request",
                "model": self.config.llm_model,
                "attempt": attempt,
                "text_length": len(text),
            },
        )

        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.config.request_timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def process(self, raw_text: str) -> Dict[str, Any]:
        last_error = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                raw_response = self._call_llm(raw_text, attempt)
                # Очистка от markdown-блоков
                clean_json = (
                    raw_response.strip()
                    .removeprefix("```json")
                    .removesuffix("```")
                    .strip()
                )
                data = json.loads(clean_json)

                # Валидация через Pydantic
                validated = ProcessedData(**data)
                # Преобразуем обратно в dict (сохраняя все поля)
                result = validated.model_dump(exclude_unset=True)
                logger.info(
                    "llm_success",
                    extra={
                        "event": "llm_success",
                        "attempt": attempt,
                        "fields": list(result.keys()),
                    },
                )
                return result

            except (
                requests.RequestException,
                json.JSONDecodeError,
                KeyError,
                ValidationError,
            ) as e:
                last_error = e
                logger.warning(
                    "llm_attempt_failed",
                    extra={
                        "event": "llm_attempt_failed",
                        "attempt": attempt,
                        "error_type": type(e).__name__,
                        "error": str(e),
                    },
                )
                if attempt < self.config.max_retries:
                    time.sleep(2**attempt)

        logger.error(
            "llm_failed",
            extra={
                "event": "llm_failed",
                "max_retries": self.config.max_retries,
                "last_error": str(last_error),
            },
        )
        raise RuntimeError(
            f"LLM processing failed after {self.config.max_retries} attempts: {last_error}"
        )
