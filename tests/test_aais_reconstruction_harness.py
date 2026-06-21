"""AAIS reconstruction harness — spec v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.aais.reconstruction.harness import ReconstructionHarness
from src.aais.reconstruction.wire import WireValidationError, load_schema, load_wire, validate_wire_record, write_wire_events

ROOT = Path(__file__).resolve().parents[1]
WIRE_SCHEMA = ROOT / "schemas" / "continuity_wire.v1.json"
PROOF_SCHEMA = ROOT / "schemas" / "continuity_proof.reconstruction.v1.json"
AAIS_FIXTURE = ROOT / "fixtures" / "fos" / "aais_lineage_reconstruction.v1.json"


def _fixture_events() -> list[dict]:
    fixture = json.loads(AAIS_FIXTURE.read_text(encoding="utf-8"))
    return list(fixture["events"])


def _write_aais_wire(path: Path) -> None:
    fixture = json.loads(AAIS_FIXTURE.read_text(encoding="utf-8"))
    write_wire_events(path, _fixture_events(), thread_id=str(fixture["thread_id"]))


def test_proof_schema_matches_spec() -> None:
    schema = json.loads(PROOF_SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["version"]["const"] == "v1"
    thread = schema["$defs"]["ThreadProof"]
    assert "lineage_ok" in thread["properties"]
    assert "invariants" in thread["properties"]


def test_wire_schema_rejects_invalid_record() -> None:
    schema = load_schema(WIRE_SCHEMA)
    with pytest.raises(WireValidationError):
        validate_wire_record({"record_type": "event", "event_id": "x"}, schema)


def test_wire_load_validates_fixture(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    _write_aais_wire(wire)
    events, threads, invalid = load_wire(wire, schema_path=WIRE_SCHEMA)
    assert len(events) == 11
    assert threads[0]["thread_id"] == "aais"
    assert not invalid


def test_harness_emits_spec_proof(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    out = tmp_path / "continuity_proof.reconstruction.json"
    _write_aais_wire(wire)
    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA), str(PROOF_SCHEMA)).run(
        output_path=out
    )

    assert proof["version"] == "v1"
    assert proof["source_wire"].startswith(str(wire))
    assert len(proof["threads"]) == 1
    thread = proof["threads"][0]
    assert thread["thread_id"] == "aais"
    assert thread["lineage_ok"] is True
    assert thread["decisions_ok"] is True
    assert thread["invariants"]["no_broken_lineage"] is True
    assert thread["invariants"]["no_unbacked_decisions"] is True
    assert thread["summary"]["decision_count"] == 2
    assert thread["summary"]["evidence_count"] == 3
    assert proof["global"]["threads_analyzed"] == 1
    assert proof["global"]["invariants"]["no_broken_lineage"] is True
    assert out.exists()


def test_harness_detects_broken_lineage(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    events = _fixture_events()
    events[1]["lineage"] = ["E999"]
    write_wire_events(wire, events, thread_id="aais")
    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA)).run()
    thread = proof["threads"][0]
    assert thread["lineage_ok"] is False
    assert thread["invariants"]["no_broken_lineage"] is False
    assert any(item["code"] == "BROKEN_LINEAGE" for item in thread["findings"])
    assert proof["global"]["invariants"]["no_broken_lineage"] is False


def test_harness_detects_unbacked_decision(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    events = _fixture_events()
    for event in events:
        if event["event_id"] == "E010":
            event["payload"] = dict(event["payload"])
            event["payload"]["evidence_refs"] = ["E404"]
    write_wire_events(wire, events, thread_id="aais")
    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA)).run()
    thread = proof["threads"][0]
    assert thread["decisions_ok"] is False
    assert thread["invariants"]["no_unbacked_decisions"] is False
    assert any(item["code"] == "UNBACKED_DECISION" for item in thread["findings"])
