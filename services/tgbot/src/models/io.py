from typing import Any

from pydantic import BaseModel


class TgbotTask(BaseModel):
    task: str
    args: dict[str, Any]


class MessageInQueue(BaseModel):
    """Model for messages in the shared queue."""

    task: TgbotTask
    api_token: str


class TaskResponse(BaseModel):
    message: str | None = None
    data: dict[str, Any] = {}


class ApiResponse(BaseModel):
    status: str
    status_code: int
    error: str | None = None
    task: TaskResponse | None = None
