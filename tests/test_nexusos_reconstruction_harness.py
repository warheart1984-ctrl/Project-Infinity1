"""NexusOS civilization-grade reconstruction — full substrate wire + URG integration."""

from __future__ import annotations

import json
from pathlib import Path

from src.aais.reconstruction.harness import ReconstructionHarness
from src.aais.reconstruction.wire import load_wire, write_merged_wire
from src.fos.integrations.nexusos import DEFAULT_NEXUSOS_THREAD, ingest_urg_mission_receipt
from src.fos.kernel import FosKernel

ROOT = Path(__file__).resolve().parents[1]
WIRE_SCHEMA = ROOT / "schemas" / "continuity_wire.v1.json"
PROOF_SCHEMA = ROOT / "schemas" / "continuity_proof.reconstruction.v1.json"
AAIS_FIXTURE = ROOT / "fixtures" / "fos" / "aais_lineage_reconstruction.v1.json"
DARZ_FIXTURE = ROOT / "fixtures" / "fos" / "darz_lineage_reconstruction.v1.json"
FOS_FIXTURE = ROOT / "fixtures" / "fos" / "fos_cross_thread_reconstruction.v1.json"
NEXUSOS_FIXTURE = ROOT / "fixtures" / "fos" / "nexusos_lineage_reconstruction.v1.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_civilization_wire(path: Path) -> dict:
    aais = _load_json(AAIS_FIXTURE)
    darz = _load_json(DARZ_FIXTURE)
    fos = _load_json(FOS_FIXTURE)
    nexusos = _load_json(NEXUSOS_FIXTURE)
    write_merged_wire(
        path,
        [
            (str(aais["thread_id"]), list(aais["events"]), None),
            (str(darz["thread_id"]), list(darz["events"]), None),
            (str(fos["thread_id"]), list(fos["events"]), fos.get("parent_thread_id")),
            (
                str(nexusos["thread_id"]),
                list(nexusos["events"]),
                nexusos.get("parent_thread_id"),
            ),
        ],
    )
    return nexusos


def test_nexusos_fixture_civilization_ground_truth() -> None:
    fixture = _load_json(NEXUSOS_FIXTURE)
    truth = fixture["ground_truth"]
    assert fixture["thread_id"] == DEFAULT_NEXUSOS_THREAD
    assert fixture["parent_thread_id"] == "fos"
    assert len(truth["governance_event_ids"]) >= 4
    assert truth["anchor_decision_id"] == "NX010"
    assert set(truth["threads"]) == {"aais", "dar-z", "fos", "nexusos"}


def test_civilization_wire_loads_four_threads(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    _write_civilization_wire(wire)
    events, threads, invalid = load_wire(wire, schema_path=WIRE_SCHEMA)
    thread_ids = {record["thread_id"] for record in threads}
    assert thread_ids == {"aais", "dar-z", "fos", "nexusos"}
    assert len(events) == 11 + 12 + 3 + 10
    nexusos_thread = next(item for item in threads if item["thread_id"] == "nexusos")
    assert nexusos_thread["parent_thread_id"] == "fos"
    assert not invalid


def test_nexusos_harness_proves_civilization_wire(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    _write_civilization_wire(wire)
    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA), str(PROOF_SCHEMA)).run()

    assert proof["global"]["threads_analyzed"] == 4
    assert proof["global"]["invariants"]["no_broken_lineage"] is True
    assert proof["global"]["invariants"]["no_orphaned_events"] is True

    by_thread = {item["thread_id"]: item for item in proof["threads"]}
    nexus = by_thread["nexusos"]
    assert nexus["lineage_ok"] is True
    assert nexus["decisions_ok"] is True
    assert nexus["summary"]["decision_count"] == 2
    assert nexus["summary"]["evidence_count"] == 2
    assert not nexus["findings"]

    assert by_thread["aais"]["lineage_ok"] is True
    assert by_thread["dar-z"]["lineage_ok"] is True
    assert by_thread["fos"]["lineage_ok"] is True


def test_nexusos_detects_broken_civilization_anchor(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    nexusos = _load_json(NEXUSOS_FIXTURE)
    events = list(nexusos["events"])
    events[7]["lineage"] = ["FOS404", "E010", "DZ010"]
    aais = _load_json(AAIS_FIXTURE)
    darz = _load_json(DARZ_FIXTURE)
    fos = _load_json(FOS_FIXTURE)
    write_merged_wire(
        wire,
        [
            (str(aais["thread_id"]), list(aais["events"]), None),
            (str(darz["thread_id"]), list(darz["events"]), None),
            (str(fos["thread_id"]), list(fos["events"]), None),
            (str(nexusos["thread_id"]), events, "fos"),
        ],
    )

    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA)).run()
    nexus = next(item for item in proof["threads"] if item["thread_id"] == "nexusos")
    assert nexus["lineage_ok"] is False
    assert any(item["code"] == "BROKEN_LINEAGE" for item in nexus["findings"])
    assert proof["global"]["invariants"]["no_broken_lineage"] is False


def test_nexusos_urg_mission_ingest_integrates_with_harness(tmp_path: Path, monkeypatch) -> None:
    wire = tmp_path / "continuity.jsonl"
    _write_civilization_wire(wire)
    monkeypatch.setenv("FOS_CONTINUITY_STORE", str(wire))

    kernel = FosKernel()
    ids = ingest_urg_mission_receipt(
        kernel,
        mission_id="mission-live-001",
        assumptions=["NX004", "NX002"],
        allowed=True,
        receipt_hash="receipt-deadbeef",
        reasons=["integration_test_pass"],
    )

    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA)).run()
    nexus = next(item for item in proof["threads"] if item["thread_id"] == "nexusos")
    assert nexus["lineage_ok"] is True
    assert nexus["decisions_ok"] is True
    assert nexus["summary"]["decision_count"] == 3
    assert nexus["summary"]["evidence_count"] == 3

    records = [json.loads(line) for line in wire.read_text(encoding="utf-8").splitlines() if line.strip()]
    decision = next(
        r for r in records if r.get("record_type") == "event" and r["event_id"] == ids["decision_event_id"]
    )
    assert decision["payload"]["mission_id"] == "mission-live-001"
    assert ids["evidence_event_id"] in decision["payload"]["evidence_refs"]
