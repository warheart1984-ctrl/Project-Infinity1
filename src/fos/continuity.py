"""FOS Continuity Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from src.fos.types import ContinuityThreadId, Id


@dataclass
class ContinuityEvent:
    thread: ContinuityThreadId
    event_id: Id
    kind: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread": self.thread,
            "event_id": self.event_id,
            "kind": self.kind,
            "payload": dict(self.payload),
        }


class ContinuityEngine:
    @staticmethod
    def emit(kind: str, thread: ContinuityThreadId, payload: dict[str, Any]) -> ContinuityEvent:
        return ContinuityEvent(
            thread=thread,
            event_id=f"evt-{uuid4()}",
            kind=kind,
            payload=payload,
        )
