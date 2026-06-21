"""FOS cross-thread reconstruction — merged AAIS + DAR-Z + FOS wire on one authority."""

from __future__ import annotations

import json
from pathlib import Path

from src.aais.reconstruction.harness import ReconstructionHarness
from src.aais.reconstruction.wire import load_wire, write_merged_wire

ROOT = Path(__file__).resolve().parents[1]
WIRE_SCHEMA = ROOT / "schemas" / "continuity_wire.v1.json"
PROOF_SCHEMA = ROOT / "schemas" / "continuity_proof.reconstruction.v1.json"
AAIS_FIXTURE = ROOT / "fixtures" / "fos" / "aais_lineage_reconstruction.v1.json"
DARZ_FIXTURE = ROOT / "fixtures" / "fos" / "darz_lineage_reconstruction.v1.json"
FOS_CROSS_FIXTURE = ROOT / "fixtures" / "fos" / "fos_cross_thread_reconstruction.v1.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_cross_thread_wire(path: Path) -> dict:
    aais = _load_json(AAIS_FIXTURE)
    darz = _load_json(DARZ_FIXTURE)
    fos = _load_json(FOS_CROSS_FIXTURE)
    write_merged_wire(
        path,
        [
            (str(aais["thread_id"]), list(aais["events"]), None),
            (str(darz["thread_id"]), list(darz["events"]), None),
            (str(fos["thread_id"]), list(fos["events"]), fos.get("parent_thread_id")),
        ],
    )
    return fos


def test_cross_thread_wire_loads_all_threads(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    _write_cross_thread_wire(wire)
    events, threads, invalid = load_wire(wire, schema_path=WIRE_SCHEMA)
    thread_ids = {record["thread_id"] for record in threads}
    assert thread_ids == {"aais", "dar-z", "fos"}
    assert len(events) == 11 + 12 + 3
    assert not invalid


def test_fos_cross_thread_harness_proves_all_threads(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    fixture = _write_cross_thread_wire(wire)
    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA), str(PROOF_SCHEMA)).run()

    assert proof["global"]["threads_analyzed"] == 3
    assert proof["global"]["invariants"]["no_broken_lineage"] is True
    assert proof["global"]["invariants"]["no_orphaned_events"] is True

    by_thread = {item["thread_id"]: item for item in proof["threads"]}
    assert set(by_thread) == {"aais", "dar-z", "fos"}

    fos_proof = by_thread["fos"]
    assert fos_proof["lineage_ok"] is True
    assert fos_proof["decisions_ok"] is True
    assert fos_proof["invariants"]["no_broken_lineage"] is True
    assert fos_proof["summary"]["decision_count"] == 1
    assert fos_proof["summary"]["evidence_count"] == 1
    assert not fos_proof["findings"]

    assert by_thread["aais"]["lineage_ok"] is True
    assert by_thread["dar-z"]["lineage_ok"] is True

    truth = fixture["ground_truth"]
    assert truth["anchor_decision_ids"]["aais"] == "E010"
    assert truth["anchor_decision_ids"]["dar-z"] == "DZ010"
    assert truth["anchor_decision_ids"]["fos"] == "FOS003"


def test_fos_cross_thread_detects_missing_peer_reference(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    fixture = _write_cross_thread_wire(wire)
    fos_events = list(fixture["events"])
    fos_events[1]["lineage"] = ["E010", "DZ404"]
    aais = _load_json(AAIS_FIXTURE)
    darz = _load_json(DARZ_FIXTURE)
    write_merged_wire(
        wire,
        [
            (str(aais["thread_id"]), list(aais["events"]), None),
            (str(darz["thread_id"]), list(darz["events"]), None),
            (str(fixture["thread_id"]), fos_events, None),
        ],
    )

    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA)).run()
    fos_proof = next(item for item in proof["threads"] if item["thread_id"] == "fos")
    assert fos_proof["lineage_ok"] is False
    assert fos_proof["invariants"]["no_broken_lineage"] is False
    assert any(item["code"] == "BROKEN_LINEAGE" for item in fos_proof["findings"])
    assert proof["global"]["invariants"]["no_broken_lineage"] is False
