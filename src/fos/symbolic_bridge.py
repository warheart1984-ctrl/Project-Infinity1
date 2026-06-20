"""Symbolic organism ↔ FOS/CAB bridge."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.continuity.cab import CABLedger, ContinuityReceipt, default_cab_store_path
from src.fos.cab_bridge import receipt_to_evidence_memory, upsert_evidence_from_receipt
from src.fos.kernel import FosKernel
from src.symbolic_organism.vm import CoherenceReceipt, ContinuityTraceStep, SymbolicState


def map_continuity_step_to_cab_fields(step: ContinuityTraceStep) -> dict[str, Any]:
    return {
        "continuity.thread_id": step.trace_id,
        "continuity.transition_id": step.step_id,
        "continuity.parent": step.parent_step,
        "continuity.transition_type": step.transition_type,
        "continuity.assumptions": list(step.assumption_id),
        "continuity.invariants": list(step.invariant_id),
        "continuity.decisions": list(step.decision_id),
        "continuity.evidence": list(step.evidence_refs),
    }


def coherence_receipt_to_cab_receipt(
    receipt: CoherenceReceipt,
    *,
    created_at: str | None = None,
) -> ContinuityReceipt:
    now = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    decision_refs = [receipt.decision_ref] if receipt.decision_ref else []
    return ContinuityReceipt(
        receipt_id=f"cab.receipt.{receipt.receipt_id}",
        identity_context={"source": "symbolic_organism", "trace_id": receipt.trace_id},
        authority_surface=["symbolic_organism.coherence"],
        event_description=f"Coherent promotion at {receipt.step_id}",
        evaluation_outcome="COHERENT",
        trace_id=receipt.trace_id,
        trace_hash="",
        proof_id=receipt.receipt_id,
        cvr_id="",
        cvr_snapshot={
            "invariants_evaluated": list(receipt.invariants_evaluated),
            "invariants_passed": list(receipt.invariants_passed),
            "obligations_resolved": list(receipt.obligations_resolved),
        },
        decision_refs=decision_refs,
        govern_policy_refs=["docs/contracts/SYMBOLIC_ORGANISM_VM_V0.md"],
        continuity_governance={"coherence_receipt": receipt.to_dict()},
        created_at=now,
    )


def ingest_symbolic_state(
    state: SymbolicState,
    *,
    kernel: FosKernel | None = None,
    ledger: CABLedger | None = None,
) -> dict[str, Any]:
    """Ingest coherence receipts and lineage from a symbolic organism run."""
    active_kernel = kernel or FosKernel()
    active_ledger = ledger or CABLedger.open(default_cab_store_path())
    ingested_receipts: list[str] = []
    ingested_evidence: list[str] = []

    for receipt in state.coherence_receipts:
        cab_receipt = coherence_receipt_to_cab_receipt(receipt)
        if active_ledger.get_latest(cab_receipt.receipt_id) is None:
            active_ledger.append(cab_receipt)
        ingested_receipts.append(cab_receipt.receipt_id)
        evidence = upsert_evidence_from_receipt(
            cab_receipt,
            memory_objects=active_kernel.memory.objects,
            thread=state.trace_id,
        )
        active_kernel.memory.upsert(evidence)
        ingested_evidence.append(evidence.id)

    return {
        "trace_id": state.trace_id,
        "lineage_steps": len(state.lineage),
        "cab_receipt_ids": ingested_receipts,
        "fos_evidence_ids": ingested_evidence,
    }
