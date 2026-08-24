from typing import List, Optional

from pydantic import BaseModel, Field


class ProcessedData(BaseModel):
    """Структурированные данные, извлечённые из текста LLM."""

    date: str = Field(
        default="unknown", description="Дата в формате ISO 8601 или 'unknown'"
    )
    summary: str = Field(default="", description="Краткое резюме на русском")
    action_items: List[str] = Field(default_factory=list, description="Список задач")
    tags: List[str] = Field(
        default_factory=list, description="Теги (3-5 ключевых слов)"
    )

    # Дополнительные поля для медицинского домена (опционально)
    patient_name: Optional[str] = Field(None, description="ФИО пациента")
    tooth: Optional[str] = Field(None, description="Номер зуба по ВОЗ")
    diagnosis: Optional[str] = Field(None, description="Код МКБ-10 + расшифровка")
    plan: Optional[List[str]] = Field(None, description="План лечения")
