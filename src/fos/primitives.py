"""FOS minimal kernel primitives — the irreducible substrate."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

Id = str
ThreadId = str


class EventType(str, Enum):
    """Minimal event types (Step 2). Everything else is payload shape."""

    CONCEPT = "Concept"
    ARCHITECTURE = "Architecture"
    GOVERNANCE = "Governance"
    DECISION = "Decision"
    EVIDENCE = "Evidence"


@dataclass
class ContinuityThread:
    """Primitive 1 — continuity spine."""

    thread_id: ThreadId
    parent_thread_id: ThreadId | None = None
    event_ids: list[Id] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "parent_thread_id": self.parent_thread_id,
            "event_ids": list(self.event_ids),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ContinuityThread:
        parent = raw.get("parent_thread_id")
        return cls(
            thread_id=str(raw["thread_id"]),
            parent_thread_id=str(parent) if parent else None,
            event_ids=[str(item) for item in (raw.get("event_ids") or [])],
        )


@dataclass
class ContinuityEvent:
    """Primitive 2 — atom of continuity."""

    event_id: Id
    thread_id: ThreadId
    event_type: str
    payload: dict[str, Any]
    timestamp: str
    lineage: list[Id] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "thread_id": self.thread_id,
            "type": self.event_type,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
            "lineage": list(self.lineage),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ContinuityEvent:
        return cls(
            event_id=str(raw["event_id"]),
            thread_id=str(raw["thread_id"]),
            event_type=str(raw.get("type") or raw.get("event_type") or "Concept"),
            payload=dict(raw.get("payload") or {}),
            timestamp=str(raw.get("timestamp") or ""),
            lineage=[str(item) for item in (raw.get("lineage") or [])],
        )


@dataclass(frozen=True)
class LineagePointer:
    """Primitive 3 — connective tissue between events."""

    from_event_id: Id
    to_event_id: Id

    def to_dict(self) -> dict[str, str]:
        return {"from_event_id": self.from_event_id, "to_event_id": self.to_event_id}

    @classmethod
    def from_lineage(cls, event_id: Id, lineage: list[Id]) -> list[LineagePointer]:
        if not lineage:
            return []
        return [cls(from_event_id=event_id, to_event_id=lineage[0])] + [
            cls(from_event_id=lineage[index], to_event_id=lineage[index + 1])
            for index in range(len(lineage) - 1)
        ]
