"""NexusOS ↔ FOS integration — URG mission receipts on the continuity wire."""

from __future__ import annotations

from typing import Any

from src.fos.kernel import FosKernel
from src.fos.primitives import EventType

DEFAULT_NEXUSOS_THREAD = "nexusos"


def ingest_urg_mission_receipt(
    kernel: FosKernel,
    *,
    mission_id: str,
    assumptions: list[str],
    thread: str = DEFAULT_NEXUSOS_THREAD,
    allowed: bool | None = True,
    receipt_hash: str | None = None,
    reasons: list[str] | None = None,
) -> dict[str, str]:
    """Append URG mission evaluation to the universal continuity wire (Evidence + Decision)."""
    engine = kernel.continuity
    engine.create_thread(thread, parent_thread_id="fos")

    evidence = engine.append_event(
        thread,
        EventType.EVIDENCE.value,
        {
            "source": "ugr-mission",
            "subsystem": "mission-receipt",
            "mission_id": mission_id,
            "allowed": allowed,
            "receipt_hash": receipt_hash,
            "reasons": reasons or [],
        },
        lineage=list(assumptions),
    )
    decision = engine.append_event(
        thread,
        EventType.DECISION.value,
        {
            "title": f"URG Mission {'Admit' if allowed else 'Block'}: {mission_id}",
            "rationale": "; ".join(reasons) if reasons else "mission ingress admitted",
            "mission_id": mission_id,
            "allowed": allowed,
            "receipt_hash": receipt_hash,
            "evidence_refs": [evidence.event_id],
        },
        lineage=[evidence.event_id, *assumptions],
    )
    return {"evidence_event_id": evidence.event_id, "decision_event_id": decision.event_id}


def export_civilization_governance(
    kernel: FosKernel,
    *,
    thread: str = DEFAULT_NEXUSOS_THREAD,
) -> list[dict[str, Any]]:
    """NexusOS consumers read governance/architecture from the wire store."""
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
