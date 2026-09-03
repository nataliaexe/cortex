from typing import Any
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    requested_action: str = Field(min_length=1, max_length=100)
    parameters: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False
