from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import AppConfig
from src.pipeline import AIPipeline


@pytest.fixture
def config(tmp_path):
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=sk-test-key\n")
    return AppConfig(_env_file=tmp_path / ".env")


@pytest.fixture
def setup_env(tmp_path):
    dirs = {
        "input": tmp_path / "data/input",
        "processed": tmp_path / "data/processed",
        "output": tmp_path / "data/output",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    (dirs["input"] / "dental_visit.txt").write_text(
        "Пациент Петров А.И. Жалобы на боль в 36 зубе. Диагностирован кариес. Назначена санация и контроль через неделю.",
        encoding="utf-8",
    )
    return dirs


def test_pipeline_e2e(config, setup_env):
    d = setup_env
    pipeline = AIPipeline(config)
    pipeline.ingestion = type(pipeline.ingestion)(d["input"], d["processed"])
    pipeline.exporter = type(pipeline.exporter)(d["output"])

    mock_llm = {
        "date": "2024-06-10",
        "summary": "Первичный осмотр, кариес 36 зуба",
        "action_items": ["Санация 36 зуба", "Контрольный осмотр через 7 дней"],
        "tags": ["стоматология", "кариес", "санация"],
    }

    with patch.object(
        pipeline.processor, "process", return_value=mock_llm
    ) as mock_proc:
        results = pipeline.run()

        assert len(results) == 1
        mock_proc.assert_called_once()

        out = results[0]
        content = out.read_text(encoding="utf-8")
        assert "Первичный осмотр" in content
        assert "- [ ] Санация 36 зуба" in content
        assert "#стоматология" in content
        assert (d["processed"] / "dental_visit.txt").exists()
