from pydantic import BaseModel, Field
from typing import Any
import uuid
from datetime import datetime, timezone


class EventPayload(BaseModel):
    type: str = Field(..., min_length=1, max_length=100, examples=["order.placed"])
    payload: dict[str, Any] = Field(default_factory=dict, examples=[{"user_id": 42}])


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    payload: dict[str, Any]
    createdAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def from_payload(cls, payload: EventPayload) -> "Event":
        return cls(type=payload.type, payload=payload.payload)


class StatsResponse(BaseModel):
    total: int
    bytes: int