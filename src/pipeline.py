import logging
from pathlib import Path
from typing import List

from src.config import AppConfig
from src.exporter import MarkdownExporter
from src.ingestion import FileIngestion
from src.processor import LLMProcessor

logger = logging.getLogger(__name__)


class AIPipeline:
    def __init__(self, config: AppConfig, prompt_path: Path | None = None):
        base = Path("data")
        self.ingestion = FileIngestion(base / "input", base / "processed")
        self.exporter = MarkdownExporter(base / "output")
        self.processor = LLMProcessor(config, prompt_path)

    def run(self) -> List[Path]:
        processed = []
        for file_path in self.ingestion.get_unprocessed_files():
            try:
                raw = self.ingestion.read_text(file_path)
                if not raw.strip():
                    logger.warning(
                        "skipping_empty",
                        extra={"event": "skipping_empty", "file": file_path.name},
                    )
                    self.ingestion.mark_processed(file_path)
                    continue

                logger.info(
                    "file_processing",
                    extra={"event": "file_processing", "file": file_path.name},
                )
                structured = self.processor.process(raw)
                out = self.exporter.export(file_path.name, structured)
                self.ingestion.mark_processed(file_path)
                processed.append(out)
                logger.info(
                    "file_success",
                    extra={
                        "event": "file_success",
                        "file": file_path.name,
                        "output": out.name,
                    },
                )
            except Exception as e:
                logger.error(
                    "file_failed",
                    extra={
                        "event": "file_failed",
                        "file": file_path.name,
                        "error": str(e),
                    },
                )
                # Не перемещаем в processed, чтобы повторить при следующем запуске
        return processed
