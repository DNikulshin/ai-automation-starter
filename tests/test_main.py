import logging
from unittest.mock import MagicMock, patch

import pytest

from src.cli import main


def test_main_exits_cleanly_when_no_files(caplog):
    caplog.set_level(logging.INFO)

    mock_config = MagicMock()
    mock_config.telegram_bot_token = ""
    mock_config.telegram_chat_id = ""

    mock_pipeline = MagicMock()
    mock_pipeline.ingestion.get_unprocessed_files.return_value = []
    mock_pipeline.run.return_value = []

    with patch("src.cli.AppConfig", return_value=mock_config), patch(
        "src.cli.AIPipeline", return_value=mock_pipeline
    ), patch("src.cli.setup_logging"):

        main()

        # Проверяем, что событие "no_files" залогировано
        assert any(record.getMessage() == "no_files" for record in caplog.records)
        mock_pipeline.run.assert_not_called()
