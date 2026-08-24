from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    # === LLM / OpenRouter ===
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    llm_model: str = Field(default="inclusionai/ring-2.6-1t:free", alias="LLM_MODEL")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")

    # === OpenRouter headers (для free-моделей) ===
    http_referer: str | None = Field(
        default="https://github.com/DNikulshin", alias="HTTP_REFERER"
    )
    app_title: str | None = Field(default="ai-automation-starter", alias="APP_TITLE")

    # === Telegram (опционально) ===
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")

    # === Mock mode (для тестов без расхода токенов) ===
    mock_llm: bool = Field(default=False, alias="MOCK_LLM")

    model_config = ConfigDict(  # type: ignore
        env_file=".env",
        populate_by_name=True,
        extra="ignore",  # ← Игнорировать неизвестные поля, чтобы не падать при добавлении новых
    )

    @field_validator("openrouter_api_key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        if not v.startswith("sk-"):
            raise ValueError("OPENROUTER_API_KEY должен начинаться с 'sk-'")
        return v
