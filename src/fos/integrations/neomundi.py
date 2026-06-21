"""NeoMundi ↔ FOS integration — measurements on the continuity wire."""

from __future__ import annotations

from typing import Any

from src.fos.kernel import FosKernel
from src.fos.primitives import EventType
from src.neomundi.measurement import NeoMundiMeasurement

DEFAULT_NEOMUNDI_THREAD = "neomundi"


def ingest_neomundi_measurement(
    kernel: FosKernel,
    measurement: NeoMundiMeasurement,
    *,
    assumptions: list[str],
    thread: str = DEFAULT_NEOMUNDI_THREAD,
    epoch_id: str | None = None,
) -> dict[str, str]:
    """Append a NeoMundi measurement as continuity Evidence on the universal wire."""
    engine = kernel.continuity
    engine.create_thread(thread, parent_thread_id="nexusos")

    evidence = engine.append_event(
        thread,
        EventType.EVIDENCE.value,
        {
            "source": measurement.source,
            "subsystem": "neomundi-measurement",
            "measurement_id": measurement.measurement_id,
            "signal_type": measurement.signal_type,
            "integrity": measurement.integrity,
            "epoch_id": epoch_id,
            "payload": dict(measurement.payload),
            "tags": list(measurement.tags),
        },
        lineage=list(assumptions),
    )
    return {"evidence_event_id": evidence.event_id}


def ingest_neomundi_measurement_record(
    kernel: FosKernel,
    record: dict[str, Any],
    *,
    assumptions: list[str],
    thread: str = DEFAULT_NEOMUNDI_THREAD,
    epoch_id: str | None = None,
) -> dict[str, str]:
    """Convenience wrapper for raw measurement dicts."""
    measurement = NeoMundiMeasurement(
        measurement_id=str(record["measurement_id"]),
        signal_type=str(record.get("signal_type") or "unknown"),
        payload=dict(record.get("payload") or {}),
        timestamp=str(record.get("timestamp") or ""),
        integrity=str(record.get("integrity") or "asserted"),
        source=str(record.get("source") or "neomundi.local"),
        tags=[str(item) for item in (record.get("tags") or [])],
    )
    return ingest_neomundi_measurement(
        kernel,
        measurement,
        assumptions=assumptions,
        thread=thread,
        epoch_id=epoch_id or record.get("epoch_id"),
    )
