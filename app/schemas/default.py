from pydantic import BaseModel
from typing import Any


class DefaultResponse(BaseModel):
    error: bool
    message: str
    payload: Any | None = None