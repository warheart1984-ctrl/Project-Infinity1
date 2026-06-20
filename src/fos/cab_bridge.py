"""FOS ↔ CAB bridge."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.continuity.cab import (
    CABLedger,
    ContinuityReceipt,
    IntentRecord,
    default_cab_store_path,
)
from src.fos.types import MemoryObject, MemoryType


def memory_to_intent(obj: MemoryObject, *, authors: list[str] | None = None) -> IntentRecord:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    intent_id = obj.id if obj.id.startswith("cab.intent.") else f"cab.intent.fos.{obj.id}"
    return IntentRecord(
        intent_id=intent_id,
        authors=list(authors or ["fos:founder"]),
        articulated_at=now,
        scope={"continuity_thread": obj.continuity_thread, "mtype": obj.mtype.value},
        problem_statement=obj.definition[:500],
        desired_outcomes=[obj.definition[:120]],
        created_at=now,
    )


def receipt_to_evidence_memory(receipt: ContinuityReceipt, *, thread: str) -> MemoryObject:
    return MemoryObject(
        id=f"mem-evidence-{receipt.receipt_id}",
        mtype=MemoryType.EVIDENCE,
        definition=receipt.event_description,
        evidence_refs=[receipt.receipt_id],
        lineage=[receipt.trace_id],
        version="v0.1.0",
        continuity_thread=thread or receipt.trace_id,
    )


def append_intent_from_memory(
    obj: MemoryObject,
    *,
    ledger: CABLedger | None = None,
    authors: list[str] | None = None,
) -> IntentRecord:
    intent = memory_to_intent(obj, authors=authors)
    active = ledger or CABLedger.open(default_cab_store_path())
    if active.get_latest(intent.intent_id) is None:
        active.append(intent)
    return intent


def upsert_evidence_from_receipt(
    receipt: ContinuityReceipt,
    *,
    memory_objects: dict[str, MemoryObject],
    thread: str = "",
) -> MemoryObject:
    obj = receipt_to_evidence_memory(receipt, thread=thread)
    memory_objects[obj.id] = obj
    return obj


def map_nova_continuity_fields(continuity_governance: dict[str, Any]) -> dict[str, Any]:
    trace = dict(continuity_governance.get("continuity_trace") or {})
    proof = dict(continuity_governance.get("proof") or {})
    return {
        "trace_id": trace.get("trace_id"),
        "step_id": trace.get("step_id"),
        "parent_step": trace.get("parent_step"),
        "transition_type": trace.get("transition_type"),
        "assumption_id": trace.get("assumption_id") or trace.get("assumptions"),
        "invariant_id": trace.get("invariant_id") or trace.get("invariants"),
        "decision_id": trace.get("decision_id") or trace.get("decisions"),
        "evidence_refs": trace.get("evidence_refs") or proof.get("evidence_refs"),
    }
