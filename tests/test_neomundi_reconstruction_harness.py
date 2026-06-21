"""NeoMundi epoch reconstruction — five-thread civilization wire + measurement ingest."""

from __future__ import annotations

import json
from pathlib import Path

from src.aais.reconstruction.harness import ReconstructionHarness
from src.aais.reconstruction.wire import load_wire, write_merged_wire
from src.fos.integrations.neomundi import DEFAULT_NEOMUNDI_THREAD, ingest_neomundi_measurement
from src.fos.kernel import FosKernel
from src.neomundi.measurement import NeoMundiMeasurement

ROOT = Path(__file__).resolve().parents[1]
WIRE_SCHEMA = ROOT / "schemas" / "continuity_wire.v1.json"
PROOF_SCHEMA = ROOT / "schemas" / "continuity_proof.reconstruction.v1.json"
AAIS_FIXTURE = ROOT / "fixtures" / "fos" / "aais_lineage_reconstruction.v1.json"
DARZ_FIXTURE = ROOT / "fixtures" / "fos" / "darz_lineage_reconstruction.v1.json"
FOS_FIXTURE = ROOT / "fixtures" / "fos" / "fos_cross_thread_reconstruction.v1.json"
NEXUSOS_FIXTURE = ROOT / "fixtures" / "fos" / "nexusos_lineage_reconstruction.v1.json"
NEOMUNDI_FIXTURE = ROOT / "fixtures" / "fos" / "neomundi_lineage_reconstruction.v1.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_epoch_wire(path: Path) -> dict:
    segments = []
    for fixture_path in (AAIS_FIXTURE, DARZ_FIXTURE, FOS_FIXTURE, NEXUSOS_FIXTURE, NEOMUNDI_FIXTURE):
        fixture = _load_json(fixture_path)
        segments.append(
            (
                str(fixture["thread_id"]),
                list(fixture["events"]),
                fixture.get("parent_thread_id"),
            )
        )
    write_merged_wire(path, segments)
    return _load_json(NEOMUNDI_FIXTURE)


def test_neomundi_fixture_epoch_ground_truth() -> None:
    fixture = _load_json(NEOMUNDI_FIXTURE)
    truth = fixture["ground_truth"]
    assert fixture["thread_id"] == DEFAULT_NEOMUNDI_THREAD
    assert fixture["parent_thread_id"] == "nexusos"
    assert truth["epoch_id"] == "epoch-2026-q3"
    assert truth["anchor_decision_id"] == "NM010"
    assert len(truth["measurement_event_ids"]) == 3
    assert set(truth["threads"]) == {"aais", "dar-z", "fos", "nexusos", "neomundi"}


def test_epoch_wire_loads_five_threads(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    _write_epoch_wire(wire)
    events, threads, invalid = load_wire(wire, schema_path=WIRE_SCHEMA)
    thread_ids = {record["thread_id"] for record in threads}
    assert thread_ids == {"aais", "dar-z", "fos", "nexusos", "neomundi"}
    assert len(events) == 11 + 12 + 3 + 10 + 10
    neomundi_thread = next(item for item in threads if item["thread_id"] == "neomundi")
    assert neomundi_thread["parent_thread_id"] == "nexusos"
    assert not invalid


def test_neomundi_harness_proves_epoch_wire(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    _write_epoch_wire(wire)
    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA), str(PROOF_SCHEMA)).run()

    assert proof["global"]["threads_analyzed"] == 5
    assert proof["global"]["invariants"]["no_broken_lineage"] is True
    assert proof["global"]["invariants"]["no_orphaned_events"] is True

    by_thread = {item["thread_id"]: item for item in proof["threads"]}
    neomundi = by_thread["neomundi"]
    assert neomundi["lineage_ok"] is True
    assert neomundi["decisions_ok"] is True
    assert neomundi["summary"]["decision_count"] == 2
    assert neomundi["summary"]["evidence_count"] == 3
    assert not neomundi["findings"]

    for thread_id in ("aais", "dar-z", "fos", "nexusos"):
        assert by_thread[thread_id]["lineage_ok"] is True


def test_neomundi_detects_broken_epoch_anchor(tmp_path: Path) -> None:
    wire = tmp_path / "continuity.jsonl"
    neomundi = _load_json(NEOMUNDI_FIXTURE)
    events = list(neomundi["events"])
    events[8]["lineage"] = ["NX404", "NM005", "NM006"]
    segments = []
    for fixture_path in (AAIS_FIXTURE, DARZ_FIXTURE, FOS_FIXTURE, NEXUSOS_FIXTURE):
        fixture = _load_json(fixture_path)
        segments.append((str(fixture["thread_id"]), list(fixture["events"]), fixture.get("parent_thread_id")))
    segments.append((str(neomundi["thread_id"]), events, neomundi.get("parent_thread_id")))
    write_merged_wire(wire, segments)

    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA)).run()
    neomundi_proof = next(item for item in proof["threads"] if item["thread_id"] == "neomundi")
    assert neomundi_proof["lineage_ok"] is False
    assert any(item["code"] == "BROKEN_LINEAGE" for item in neomundi_proof["findings"])
    assert proof["global"]["invariants"]["no_broken_lineage"] is False


def test_neomundi_measurement_ingest_integrates_with_harness(tmp_path: Path, monkeypatch) -> None:
    wire = tmp_path / "continuity.jsonl"
    _write_epoch_wire(wire)
    monkeypatch.setenv("FOS_CONTINUITY_STORE", str(wire))

    kernel = FosKernel()
    result = ingest_neomundi_measurement(
        kernel,
        NeoMundiMeasurement(
            measurement_id="nm.live.epoch-signal-001",
            signal_type="continuity_invariant",
            payload={"gate": "aais-reconstruction-gate", "status": "pass"},
            timestamp="2026-12-20T00:00:00Z",
            integrity="verified",
            source="neomundi",
        ),
        assumptions=["NM004", "NM008"],
        epoch_id="epoch-2026-q3",
    )

    proof = ReconstructionHarness(str(wire), str(WIRE_SCHEMA)).run()
    neomundi = next(item for item in proof["threads"] if item["thread_id"] == "neomundi")
    assert neomundi["lineage_ok"] is True
    assert neomundi["decisions_ok"] is True
    assert neomundi["summary"]["evidence_count"] == 4

    records = [json.loads(line) for line in wire.read_text(encoding="utf-8").splitlines() if line.strip()]
    evidence = next(
        r for r in records if r.get("record_type") == "event" and r["event_id"] == result["evidence_event_id"]
    )
    assert evidence["type"] == "Evidence"
    assert evidence["payload"]["measurement_id"] == "nm.live.epoch-signal-001"
    assert evidence["payload"]["epoch_id"] == "epoch-2026-q3"
