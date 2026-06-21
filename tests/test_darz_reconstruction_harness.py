"""DAR-Z reconstruction harness — governance-heavy fixture + wire integration."""

from __future__ import annotations

import json
from pathlib import Path

from src.aais.reconstruction.harness import ReconstructionHarness
from src.aais.reconstruction.wire import load_wire, write_wire_events
from src.fos.integrations.darz import DEFAULT_DARZ_THREAD, ingest_darz_trace
from src.fos.kernel import FosKernel

ROOT = Path(__file__).resolve().parents[1]
WIRE_SCHEMA = ROOT / "schemas" / "continuity_wire.v1.json"
PROOF_SCHEMA = ROOT / "schemas" / "continuity_proof.reconstruction.v1.json"
DARZ_FIXTURE = ROOT / "fixtures" / "fos" / "darz_lineage_reconstruction.v1.json"


def _load_fixture() -> dict:
    return json.loads(DARZ_FIXTURE.read_text(encoding="utf-8"))


def _write_darz_wire(path: Path) -> dict:
    fixture = _load_fixture()
    write_wire_events(path, list(fixture["events"]), thread_id=str(fixture["thread_id"]))
    return fixture


def test_darz_fixture_ground_truth_structure() -> None:
    fixture = _load_fixture()
    truth = fixture["ground_truth"]
    assert fixture["thread_id"] == DEFAULT_DARZ_THREAD
    assert len(truth["governance_event_ids"]) >= 3
    assert truth["policy_bundle_event_id"] == "DZ003"
    assert truth["anchor_decision_id"] == "DZ010"
    assert set(truth["execute_decision_ids"]) <= set(truth["decision_event_ids"])
    assert set(truth["block_decision_ids"]) <= set(truth["decision_event_ids"])


def test_darz_wire_loads_fixture(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    fixture = _write_darz_wire(wire)
    events, threads, invalid = load_wire(wire, schema_path=WIRE_SCHEMA)
    assert len(events) == len(fixture["events"])
    assert threads[0]["thread_id"] == "dar-z"
    assert not invalid


def test_darz_harness_emits_clean_proof(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    _write_darz_wire(wire)
    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA), str(PROOF_SCHEMA)).run()

    thread = proof["threads"][0]
    assert thread["thread_id"] == "dar-z"
    assert thread["lineage_ok"] is True
    assert thread["decisions_ok"] is True
    assert thread["invariants"]["no_orphaned_events"] is True
    assert thread["invariants"]["no_broken_lineage"] is True
    assert thread["invariants"]["no_unbacked_decisions"] is True
    assert thread["summary"]["decision_count"] == 3
    assert thread["summary"]["evidence_count"] == 3
    assert thread["summary"]["first_event"] == "DZ001"
    assert thread["summary"]["last_event"] == "DZ012"
    assert proof["global"]["invariants"]["no_broken_lineage"] is True
    assert not thread["findings"]


def test_darz_harness_detects_governance_break_unbacked_block(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    fixture = _load_fixture()
    events = list(fixture["events"])
    for event in events:
        if event["event_id"] == "DZ012":
            event["payload"] = dict(event["payload"])
            event["payload"]["evidence_refs"] = ["DZ404"]
    write_wire_events(wire, events, thread_id="dar-z")

    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA)).run()
    thread = proof["threads"][0]
    assert thread["decisions_ok"] is False
    assert thread["invariants"]["no_unbacked_decisions"] is False
    assert any(item["code"] == "UNBACKED_DECISION" for item in thread["findings"])


def test_darz_ingest_trace_integrates_with_harness(tmp_path: Path, monkeypatch) -> None:
    """Live DAR-Z ingest appends to fixture wire; harness still proves continuity."""
    wire = tmp_path / "continuity.jsonl"
    _write_darz_wire(wire)
    monkeypatch.setenv("FOS_CONTINUITY_STORE", str(wire))

    kernel = FosKernel()
    ids = ingest_darz_trace(
        kernel,
        trace_id="proposal-003",
        assumptions=["DZ004", "DZ008"],
        thread=DEFAULT_DARZ_THREAD,
        allowed=True,
        replay_hash="live-9x8y7z",
        reasons=["integration_test_pass"],
    )

    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA)).run()
    thread = proof["threads"][0]

    assert thread["lineage_ok"] is True
    assert thread["decisions_ok"] is True
    assert thread["invariants"]["no_unbacked_decisions"] is True
    assert thread["summary"]["decision_count"] == 4
    assert thread["summary"]["evidence_count"] == 4

    records = [json.loads(line) for line in wire.read_text(encoding="utf-8").splitlines() if line.strip()]
    decision = next(
        r for r in records if r.get("record_type") == "event" and r["event_id"] == ids["decision_event_id"]
    )
    assert decision["type"] == "Decision"
    assert decision["payload"]["allowed"] is True
    assert ids["evidence_event_id"] in decision["payload"]["evidence_refs"]
