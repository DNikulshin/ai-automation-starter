import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.config import AppConfig
from src.processor import LLMProcessor


@pytest.fixture
def config(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("OPENROUTER_API_KEY=sk-test-key\n")
    return AppConfig(_env_file=env_file)


@pytest.fixture
def processor(config, tmp_path):
    prompt_file = tmp_path / "test_prompt.yaml"
    prompt_file.write_text("system: test\ntemplate: '{text}'\n")
    return LLMProcessor(config, prompt_file)


def _mock_response(content: str, status_code: int = 200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status_code}")
    return resp


# ------------------------------------------------------------
# 1. Тест валидного JSON
# ------------------------------------------------------------
@patch("src.processor.requests.post")
def test_process_valid_json(mock_post, processor):
    mock_post.return_value = _mock_response(
        json.dumps(
            {"date": "2024-01-01", "summary": "Тестовое резюме", "tags": ["test"]}
        )
    )
    result = processor.process("sample text")
    assert result["date"] == "2024-01-01"
    assert result["summary"] == "Тестовое резюме"
    assert mock_post.call_count == 1


# ------------------------------------------------------------
# 2. Тест повторных попыток при кривом JSON
# ------------------------------------------------------------
@patch("src.processor.requests.post")
def test_process_malformed_json_retry(mock_post, processor):
    mock_post.side_effect = [
        _mock_response("not json"),
        _mock_response("{broken"),
        _mock_response(json.dumps({"summary": "OK", "tags": ["ok"]})),
    ]
    result = processor.process("sample")
    assert result["summary"] == "OK"
    assert mock_post.call_count == 3


# ------------------------------------------------------------
# 3. Тест ошибки сети – исчерпание попыток
# ------------------------------------------------------------
@patch("src.processor.requests.post")
def test_process_api_error_retry_limit(mock_post, processor):
    mock_post.side_effect = requests.RequestException("Network error")

    with pytest.raises(RuntimeError, match="failed after 3 attempts"):
        processor.process("sample")

    assert mock_post.call_count == 3
