"""Continuity wire is the universal language — Rust and Python share one JSONL authority."""

from __future__ import annotations

import json
from pathlib import Path

from src.fos.continuity import ContinuityEngine
from src.fos.integrations.darz import DEFAULT_DARZ_THREAD, ingest_darz_trace
from src.fos.kernel import FosKernel
from src.fos.primitives import EventType


def test_python_writes_rust_can_read_shape(tmp_path: Path) -> None:
    store = tmp_path / "continuity.jsonl"
    engine = ContinuityEngine(store_path=store)
    engine.create_thread(DEFAULT_DARZ_THREAD)
    engine.append_event(
        DEFAULT_DARZ_THREAD,
        EventType.EVIDENCE.value,
        {"source": "python-fos", "note": "wire bootstrap"},
        lineage=[],
        event_id="evt-py-001",
    )

    lines = store.read_text(encoding="utf-8").strip().splitlines()
    event_line = json.loads(lines[-1])
    assert event_line["record_type"] == "event"
    assert event_line["event_id"] == "evt-py-001"
    assert event_line["type"] == "Evidence"
    assert event_line["thread_id"] == DEFAULT_DARZ_THREAD


def test_darz_ingest_writes_evidence_and_decision(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "continuity.jsonl"
    monkeypatch.setenv("FOS_CONTINUITY_STORE", str(store))

    kernel = FosKernel()
    ids = ingest_darz_trace(
        kernel,
        trace_id="proposal-001",
        assumptions=["evt-prior"],
        thread=DEFAULT_DARZ_THREAD,
        allowed=True,
        replay_hash="abc123",
    )

    records = [json.loads(line) for line in store.read_text(encoding="utf-8").splitlines() if line.strip()]
    event_records = [r for r in records if r.get("record_type") == "event"]
    assert len(event_records) == 2
    assert ids["evidence_event_id"] in {r["event_id"] for r in event_records}
    assert ids["decision_event_id"] in {r["event_id"] for r in event_records}

    decision = next(r for r in event_records if r["event_id"] == ids["decision_event_id"])
    assert decision["type"] == "Decision"
    assert decision["payload"]["allowed"] is True
