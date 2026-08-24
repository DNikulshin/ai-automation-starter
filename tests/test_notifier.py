from unittest.mock import MagicMock, patch

import pytest
import requests

from src.notifier import TelegramNotifier


@pytest.fixture
def notifier():
    return TelegramNotifier(bot_token="test-token", chat_id="123", enabled=True)


@patch("src.notifier.requests.post")
def test_send_success(mock_post, notifier):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    result = notifier.send("Test message")

    assert result is True
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args[1]["json"]
    assert call_kwargs["chat_id"] == "123"
    assert "Test message" in call_kwargs["text"]


@patch("src.notifier.requests.post")
def test_send_disabled(mock_post, notifier):
    notifier.enabled = False
    result = notifier.send("Test")
    assert result is False
    mock_post.assert_not_called()


@patch("src.notifier.requests.post")
def test_send_network_error(mock_post, notifier):
    mock_post.side_effect = requests.RequestException("Timeout")
    result = notifier.send("Test")
    assert result is False
    mock_post.assert_called_once()


@patch("src.notifier.requests.post")
def test_notify_success_business_format(mock_post, notifier):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    notifier.notify_success(
        "dental.txt",
        {
            "patient_name": "Иванов И.И.",
            "date": "2026-05-11",
            "summary": "Первичный осмотр",
        },
    )

    call_args = mock_post.call_args[1]["json"]["text"]
    assert "Иванов И.И." in call_args
    assert "2026-05-11" in call_args
    assert "data/output" not in call_args  # ✅ путь скрыт
