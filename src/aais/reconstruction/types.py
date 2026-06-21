"""Typed objects for ContinuityProof.reconstruction (spec v1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

REPLAY_KINDS = frozenset({"Evidence", "Decision", "Error", "Correction", "Override"})
META_KINDS = frozenset({"Meta", "Concept", "Note", "Architecture", "Governance", "Legacy", "Invariant"})


@dataclass(frozen=True)
class ContinuityEvent:
    thread_id: str
    event_id: str
    parent_event_id: str | None
    timestamp: datetime
    kind: str
    lineage: dict[str, Any]
    payload: dict[str, Any]

    @property
    def causal_lineage(self) -> tuple[str, ...]:
        causal = self.lineage.get("causal")
        if isinstance(causal, list):
            return tuple(str(item) for item in causal)
        return ()


@dataclass
class LineageGraph:
    thread_id: str
    events: dict[str, ContinuityEvent] = field(default_factory=dict)
    roots: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    broken_lineage: list[dict[str, str]] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)

    def ordered_events(self) -> list[ContinuityEvent]:
        return sorted(self.events.values(), key=lambda event: (event.timestamp, event.event_id))


@dataclass
class ThreadProof:
    thread_id: str
    events_replayed: int
    lineage_ok: bool
    evidence_ok: bool
    decisions_ok: bool
    invariants: dict[str, bool]
    summary: dict[str, Any]
    findings: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "events_replayed": self.events_replayed,
            "lineage_ok": self.lineage_ok,
            "evidence_ok": self.evidence_ok,
            "decisions_ok": self.decisions_ok,
            "invariants": dict(self.invariants),
            "summary": dict(self.summary),
            "findings": list(self.findings),
        }


@dataclass
class ContinuityProofReconstruction:
    version: str
    generated_at: str
    source_wire: str
    threads: list[ThreadProof]
    global_: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "source_wire": self.source_wire,
            "threads": [thread.to_dict() for thread in self.threads],
            "global": dict(self.global_),
        }
