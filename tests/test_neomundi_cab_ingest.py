"""NeoMundi → CAB ingest tests."""

from __future__ import annotations

from src.continuity.cab import CABLedger
from src.neomundi.adapter import parse_measurement_record
from src.neomundi.ingest import ingest_measurement


def test_ingest_measurement_creates_evidence_chain():
    ledger = CABLedger()
    measurement = parse_measurement_record(
        {
            "measurement_id": "nm.eco.water-level-001",
            "signal_type": "ecological",
            "payload": {"region": "delta", "level_m": 1.2},
            "timestamp": "2026-06-19T14:00:00Z",
            "integrity": "sensor-validated",
        }
    )
    chain = ingest_measurement(measurement, ledger=ledger)
    assert chain.chain_id == "cab.evidence.neomundi.nm.eco.water-level-001"
    assert chain.neomundi_measurement_refs == ["nm.eco.water-level-001"]
    assert ledger.get_latest(chain.chain_id) is not None


def test_duplicate_ingest_is_idempotent():
    ledger = CABLedger()
    measurement = parse_measurement_record(
        {
            "measurement_id": "nm.dup.001",
            "signal_type": "cultural",
            "payload": {"theme": "continuity"},
            "timestamp": "2026-06-19T14:01:00Z",
        }
    )
    first = ingest_measurement(measurement, ledger=ledger)
    second = ingest_measurement(measurement, ledger=ledger)
    assert first.chain_id == second.chain_id
    assert len(ledger.entries) == 1
