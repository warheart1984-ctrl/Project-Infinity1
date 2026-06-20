"""CAB section for ControlTower operator console."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.continuity.cab import (
    CABLedger,
    CABObjectType,
    default_cab_store_path,
    load_cab_scenario,
    populate_ledger_from_scenario,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _known_gaps_from_fixture() -> list[str]:
    fixture = _repo_root() / "fixtures" / "cab" / "governance_lineage_demo.v1.yaml"
    if not fixture.is_file():
        return []
    scenario = load_cab_scenario(fixture)
    for plan in scenario.get("reconstruction_plans") or []:
        gaps = plan.get("known_gaps") or []
        return [str(item) for item in gaps]
    return []


def _summary_for_payload(object_type: CABObjectType, payload: dict[str, Any]) -> str:
    if object_type == CABObjectType.INTENT:
        return str(payload.get("problem_statement") or payload.get("intent_id") or "")[:120]
    if object_type == CABObjectType.DECISION:
        return f"{payload.get('chosen_option')}: {payload.get('rationale', '')}"[:120]
    if object_type == CABObjectType.CONTINUITY_RECEIPT:
        return str(payload.get("event_description") or payload.get("receipt_id") or "")[:120]
    if object_type == CABObjectType.EVIDENCE_CHAIN:
        refs = payload.get("neomundi_measurement_refs") or []
        return f"chain sources={len(payload.get('sources') or [])} neomundi={len(refs)}"
    return str(payload.get("object_id") or "")[:120]


def _recent_entries(
    ledger: CABLedger,
    object_type: CABObjectType,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    entries = ledger.list_by_type(object_type)
    recent = entries[-limit:] if limit else entries
    items: list[dict[str, Any]] = []
    for entry in reversed(recent):
        items.append(
            {
                "object_id": entry.object_id,
                "object_type": entry.object_type.value,
                "created_at": entry.created_at,
                "summary": _summary_for_payload(entry.object_type, entry.payload),
            }
        )
    return items


def build_lineage_links(ledger: CABLedger, *, limit: int = 20) -> list[dict[str, str]]:
    """Intent → decision → receipt edges for console graph."""
    links: list[dict[str, str]] = []
    intents = ledger.list_by_type(CABObjectType.INTENT)[-limit:]
    for intent_entry in intents:
        intent_id = intent_entry.object_id
        for decision_id in intent_entry.payload.get("decision_refs") or []:
            links.append({"from": intent_id, "to": decision_id, "kind": "intent_decision"})
            decision = ledger.get_latest(decision_id)
            if decision is None:
                continue
            for receipt_id in decision.payload.get("continuity_receipt_refs") or []:
                links.append({"from": decision_id, "to": receipt_id, "kind": "decision_receipt"})
    return links


def build_cab_console_section(*, limit: int = 10, ledger: CABLedger | None = None) -> dict[str, Any]:
    active = ledger or CABLedger.open(default_cab_store_path())
    store_path = str(active.store_path or default_cab_store_path())
    counts = {
        object_type.value: len(active.list_by_type(object_type))
        for object_type in CABObjectType
    }
    override_gaps = os.environ.get("CAB_KNOWN_GAPS", "").strip()
    known_gaps = [part.strip() for part in override_gaps.split(";") if part.strip()]
    if not known_gaps:
        known_gaps = _known_gaps_from_fixture()
    return {
        "status": "ok",
        "runtime_effect": "readout_only",
        "store_path": store_path,
        "object_counts": counts,
        "recent_intents": _recent_entries(active, CABObjectType.INTENT, limit=limit),
        "recent_decisions": _recent_entries(active, CABObjectType.DECISION, limit=limit),
        "recent_receipts": _recent_entries(active, CABObjectType.CONTINUITY_RECEIPT, limit=limit),
        "lineage_links": build_lineage_links(active, limit=limit),
        "known_gaps": known_gaps,
    }


def seed_demo_ledger_if_empty(ledger: CABLedger | None = None) -> CABLedger:
    """Load governance demo fixture when store is empty (tests/dev)."""
    active = ledger or CABLedger.open(default_cab_store_path())
    if active.entries:
        return active
    fixture = _repo_root() / "fixtures" / "cab" / "governance_lineage_demo.v1.yaml"
    if fixture.is_file():
        scenario = load_cab_scenario(fixture)
        return populate_ledger_from_scenario(scenario)
    return active
