import logging
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


class FileIngestion:
    def __init__(self, input_dir: Path, processed_dir: Path | None = None):
        self.input_dir = input_dir
        self.processed_dir = processed_dir or input_dir.parent / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def get_unprocessed_files(self) -> Iterator[Path]:
        self.input_dir.mkdir(parents=True, exist_ok=True)
        for file_path in self.input_dir.glob("*.txt"):
            if (
                file_path.is_file()
                and not (self.processed_dir / file_path.name).exists()
            ):
                yield file_path

    def read_text(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 failed for {file_path.name}, fallback to latin-1")
            return file_path.read_text(encoding="latin-1")

    def mark_processed(self, file_path: Path) -> None:
        target = self.processed_dir / file_path.name
        file_path.rename(target)
        logger.info(f"✅ Marked as processed: {target.name}")
