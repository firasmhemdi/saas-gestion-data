from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssistantQuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=600)


class AssistantAnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    sources: list[dict[str, Any]]
    created_at: datetime
