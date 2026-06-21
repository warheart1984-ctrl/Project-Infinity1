"""DAR-Z ↔ FOS integration — coupled via continuity wire (JSONL), not FFI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.fos.continuity import ContinuityEngine, default_continuity_store_path
from src.fos.kernel import FosKernel
from src.fos.primitives import EventType
from src.fos.types import MemoryObject, MemoryType

DEFAULT_DARZ_THREAD = "dar-z"


def continuity_store_path() -> Path:
    return default_continuity_store_path()


def export_concepts_for_darz(kernel: FosKernel, *, thread: str = DEFAULT_DARZ_THREAD) -> list[dict[str, Any]]:
    """DAR-Z consumes concept/invariant/architecture/governance from the wire store."""
    engine = kernel.continuity
    return [
        {
            "event_id": event.event_id,
            "type": event.event_type,
            "payload": event.payload,
            "lineage": event.lineage,
        }
        for event in engine.query_thread(thread)
        if event.event_type
        in {
            EventType.CONCEPT.value,
            EventType.ARCHITECTURE.value,
            EventType.GOVERNANCE.value,
            "Invariant",
        }
    ]


def ingest_darz_trace(
    kernel: FosKernel,
    *,
    trace_id: str,
    assumptions: list[str],
    thread: str = DEFAULT_DARZ_THREAD,
    allowed: bool | None = None,
    replay_hash: str | None = None,
    reasons: list[str] | None = None,
) -> dict[str, str]:
    """Append DAR-Z evaluation to the universal continuity wire (Evidence + Decision)."""
    engine = kernel.continuity
    engine.create_thread(thread)

    evidence = engine.append_event(
        thread,
        EventType.EVIDENCE.value,
        {
            "source": "darz-kernel",
            "subsystem": "execution-audit",
            "trace_id": trace_id,
            "allowed": allowed,
            "replay_hash": replay_hash,
            "reasons": reasons or [],
        },
        lineage=list(assumptions),
    )
    decision = engine.append_event(
        thread,
        EventType.DECISION.value,
        {
            "title": f"DAR-Z {'Execute' if allowed else 'Block'}: {trace_id}",
            "rationale": "; ".join(reasons) if reasons else "kernel execution admitted",
            "source_message_id": trace_id,
            "allowed": allowed,
            "replay_hash": replay_hash,
            "evidence_refs": [evidence.event_id],
        },
        lineage=[evidence.event_id, *assumptions],
    )
    return {"evidence_event_id": evidence.event_id, "decision_event_id": decision.event_id}


def load_wire_events(path: Path | None = None) -> list[dict[str, Any]]:
    """Read raw wire records — any language can write, any language can read."""
    store = path or continuity_store_path()
    if not store.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in store.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if cleaned:
            records.append(json.loads(cleaned))
    return records


def ingest_darz_trace_legacy(
    kernel: FosKernel,
    *,
    trace_id: str,
    assumptions: list[str],
    thread: str,
) -> MemoryObject:
    """Legacy memory projection — prefer ingest_darz_trace for wire authority."""
    ingest_darz_trace(kernel, trace_id=trace_id, assumptions=assumptions, thread=thread)
    obj = MemoryObject(
        id=f"mem-darz-{trace_id}",
        mtype=MemoryType.EVIDENCE,
        definition=f"DAR-Z trace {trace_id}",
        evidence_refs=[trace_id],
        lineage=assumptions,
        continuity_thread=thread,
    )
    kernel.memory.upsert(obj)
    return obj
