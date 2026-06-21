"""Backward-compatible entry — AAIS harness is canonical."""

from __future__ import annotations

import json
from pathlib import Path

from src.aais.reconstruction.harness import ReconstructionHarness
from src.aais.reconstruction.wire import write_wire_events

REPO_ROOT = Path(__file__).resolve().parents[3]
AAIS_FIXTURE = REPO_ROOT / "fixtures" / "fos" / "aais_lineage_reconstruction.v1.json"
WIRE_SCHEMA = REPO_ROOT / "schemas" / "continuity_wire.v1.json"


def run_aais_reconstruction_harness(store_path: Path | None = None) -> dict:
    fixture = json.loads(AAIS_FIXTURE.read_text(encoding="utf-8"))
    wire_path = store_path or REPO_ROOT / ".runtime" / "aais" / "continuity.jsonl"
    write_wire_events(wire_path, list(fixture["events"]), thread_id=str(fixture["thread_id"]))
    return ReconstructionHarness(wire_path, wire_schema_path=WIRE_SCHEMA).run()
