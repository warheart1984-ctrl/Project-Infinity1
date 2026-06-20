"""NeoMundi measurement → CAB EvidenceChain ingest."""

from __future__ import annotations

from datetime import datetime, timezone

from src.continuity.cab import CABLedger, EvidenceChain, default_cab_store_path
from src.neomundi.measurement import NeoMundiMeasurement


def chain_id_for_measurement(measurement_id: str) -> str:
    return f"cab.evidence.neomundi.{measurement_id}"


def ingest_measurement(
    measurement: NeoMundiMeasurement,
    *,
    ledger: CABLedger | None = None,
    decision_refs: list[str] | None = None,
    assumption_refs: list[str] | None = None,
) -> EvidenceChain:
    """Create and append a CAB EvidenceChain from a NeoMundi measurement."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    chain_id = chain_id_for_measurement(measurement.measurement_id)
    chain = EvidenceChain(
        chain_id=chain_id,
        neomundi_measurement_refs=[measurement.measurement_id],
        sources=[measurement.source, f"signal:{measurement.signal_type}"],
        methods=["neomundi measurement ingest"],
        integrity_assessment=measurement.integrity,
        assumption_refs=list(assumption_refs or []),
        decision_refs=list(decision_refs or []),
        continuity_receipt_refs=[],
        created_at=measurement.timestamp or now,
    )
    active = ledger or CABLedger.open(default_cab_store_path())
    if active.get_latest(chain_id) is None:
        active.append(chain)
    return chain
