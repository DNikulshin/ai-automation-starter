import logging
import os
import sys
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter  # <-- новый импорт

from src.config import AppConfig
from src.notifier import TelegramNotifier
from src.pipeline import AIPipeline


def setup_logging(log_file: Path | None = None):
    """Настройка структурированного логирования в JSON."""
    level = logging.INFO
    handlers: list[logging.Handler] = []

    # Вывод в stdout в JSON
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        rename_fields={"levelname": "severity", "asctime": "timestamp"},
    )
    stdout_handler.setFormatter(formatter)
    handlers.append(stdout_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )


def main():
    setup_logging(Path("logs/automation.log"))
    logger = logging.getLogger(__name__)

    try:
        config = AppConfig()
        logger.info(
            "config_loaded",
            extra={
                "event": "config_loaded",
                "model": config.llm_model,
                "max_retries": config.max_retries,
                "telegram_enabled": bool(
                    config.telegram_bot_token and config.telegram_chat_id
                ),
            },
        )
    except Exception as e:
        logger.error("config_failed", extra={"event": "config_failed", "error": str(e)})
        sys.exit(1)

    prompt_path = None
    if env_prompt := os.getenv("PROMPT_PATH"):
        prompt_path = Path(env_prompt)
        if prompt_path.exists():
            logger.info(
                "custom_prompt_used",
                extra={"event": "custom_prompt_used", "path": str(prompt_path)},
            )
        else:
            logger.warning(
                "custom_prompt_not_found",
                extra={"event": "custom_prompt_not_found", "path": str(prompt_path)},
            )
            prompt_path = None

    notifier = TelegramNotifier(
        bot_token=config.telegram_bot_token or "",
        chat_id=config.telegram_chat_id or "",
        enabled=bool(config.telegram_bot_token and config.telegram_chat_id),
    )

    pipeline = AIPipeline(config, prompt_path=prompt_path)

    unprocessed = list(pipeline.ingestion.get_unprocessed_files())
    notifier.notify_startup(len(unprocessed))

    if not unprocessed:
        logger.info("no_files", extra={"event": "no_files"})
        return

    logger.info(
        "processing_start",
        extra={"event": "processing_start", "file_count": len(unprocessed)},
    )

    success_count = 0
    failed_count = 0
    try:
        results = pipeline.run()
        success_count = len(results)
        logger.info(
            "processing_finished",
            extra={"event": "processing_finished", "success": success_count},
        )

        for out_path in results:
            import yaml

            meta = {}
            try:
                content = out_path.read_text(encoding="utf-8")
                if content.startswith("---"):
                    frontmatter = content.split("---")[1]
                    meta = yaml.safe_load(frontmatter) or {}
            except Exception:
                pass
            notifier.notify_success(out_path.stem + ".txt", meta)

    except Exception as e:
        logger.error(
            "pipeline_crash",
            extra={"event": "pipeline_crash", "error": str(e)},
            exc_info=True,
        )
        notifier.notify_error("system", str(e))
        sys.exit(2)
    finally:
        notifier.notify_daily_summary(success_count, failed_count)


if __name__ == "__main__":
    main()
