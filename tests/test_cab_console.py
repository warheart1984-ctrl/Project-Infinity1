"""ControlTower CAB console section tests."""

from __future__ import annotations

from src.continuity.cab import load_cab_scenario, populate_ledger_from_scenario
from src.continuity.cab_console import build_cab_console_section
from src.ugr.operator_console.snapshot import CONSOLE_VERSION, build_operator_console_snapshot
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_DEMO = ROOT / "fixtures" / "cab" / "governance_lineage_demo.v1.yaml"


def test_cab_console_section_lists_recent_decisions():
    scenario = load_cab_scenario(GOVERNANCE_DEMO)
    ledger = populate_ledger_from_scenario(scenario)
    section = build_cab_console_section(limit=5, ledger=ledger)
    assert section["status"] == "ok"
    assert section["recent_decisions"]
    assert any(item["object_id"].startswith("cab.decision.") for item in section["recent_decisions"])
    assert section["lineage_links"]


def test_operator_snapshot_includes_cab_section(monkeypatch):
    monkeypatch.setenv("CAB_STORE", str(ROOT / ".runtime-test-cab" / "ledger.jsonl"))
    from src.continuity.cab import CABLedger, default_cab_store_path

    store = default_cab_store_path()
    store.parent.mkdir(parents=True, exist_ok=True)
    if store.exists():
        store.unlink()
    scenario = load_cab_scenario(GOVERNANCE_DEMO)
    ledger = populate_ledger_from_scenario(scenario)
    ledger.store_path = store
    for entry in ledger.entries:
        ledger._persist_entry(entry)

    snapshot = build_operator_console_snapshot(runtime=None)
    assert snapshot["console_version"] == CONSOLE_VERSION
    assert "cab" in snapshot
    assert snapshot["cab"].get("recent_decisions") is not None
