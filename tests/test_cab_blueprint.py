"""CAB blueprint tests — ontology, ledger, invariants, Nova receipt ingest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.continuity.cab import (
    CABLedger,
    DecisionRecord,
    IntentRecord,
    ingest_nova_continuity_governance,
    load_cab_scenario,
    populate_ledger_from_scenario,
)
from src.continuity.cab_invariants import evaluate_cab_invariants

ROOT = Path(__file__).resolve().parents[1]
CAB_SCHEMA = ROOT / "schemas" / "cab.v1.json"
GOVERNANCE_DEMO = ROOT / "fixtures" / "cab" / "governance_lineage_demo.v1.yaml"


@pytest.fixture
def cab_schema() -> dict:
    return json.loads(CAB_SCHEMA.read_text(encoding="utf-8"))


@pytest.fixture
def governance_ledger() -> CABLedger:
    scenario = load_cab_scenario(GOVERNANCE_DEMO)
    return populate_ledger_from_scenario(scenario)


def test_cab_schema_defines_eight_object_types(cab_schema):
    defs = cab_schema["$defs"]
    expected = {
        "IntentRecord",
        "DecisionRecord",
        "AssumptionRecord",
        "EvidenceChain",
        "ContinuityReceipt",
        "FounderKnowledgeSnapshot",
        "SuccessionProtocol",
        "ReconstructionPlan",
    }
    assert expected.issubset(set(defs.keys()))


def test_governance_lineage_demo_passes_cab_invariants(governance_ledger):
    report = evaluate_cab_invariants(governance_ledger)
    assert report.passed, report.to_dict()


def test_cab_ledger_supersede_preserves_non_erasure():
    ledger = CABLedger()
    intent_v1 = IntentRecord(
        intent_id="cab.intent.test",
        authors=["steward:a"],
        articulated_at="2026-06-19T10:00:00Z",
        scope={"system": "test"},
        problem_statement="initial",
        desired_outcomes=["v1"],
        created_at="2026-06-19T10:00:00Z",
    )
    ledger.append(intent_v1)
    intent_v2 = IntentRecord(
        intent_id="cab.intent.test.v2",
        authors=["steward:a"],
        articulated_at="2026-06-19T11:00:00Z",
        scope={"system": "test"},
        problem_statement="refined",
        desired_outcomes=["v2"],
        prior_intent_refs=["cab.intent.test"],
        created_at="2026-06-19T11:00:00Z",
    )
    ledger.supersede("cab.intent.test", intent_v2)
    assert len(ledger.entries) == 2
    old = ledger.get_latest("cab.intent.test")
    assert old is not None
    assert old.superseded
    assert old.payload.get("superseded_by") == "cab.intent.test.v2"


def test_ingest_nova_continuity_governance():
    ledger = CABLedger()
    continuity_governance = {
        "proof": {
            "proof_id": "proof.nova.test",
            "status": "PROVEN",
            "law_surfaces": ["aais.law.runtime.system", "ugr.continuity"],
            "replay_fingerprint": "a" * 64,
        },
        "cvr": {"cvr_id": "cvr.nova:test", "derived_score": 0.75, "law_surfaces": ["ugr.continuity"]},
        "continuity_trace": {
            "trace_id": "ct.nova.test",
            "trace_hash": "b" * 64,
        },
    }
    receipt = ingest_nova_continuity_governance(
        trace_id="nova-turn-test",
        identity_context={"instance_id": "nova-test", "tenant_id": "local"},
        continuity_governance=continuity_governance,
        event_description="test lawful turn",
        created_at="2026-06-19T12:00:00Z",
        decision_refs=["cab.decision.nova-in-urg"],
        ledger=ledger,
    )
    assert receipt.proof_id == "proof.nova.test"
    assert receipt.cvr_id == "cvr.nova:test"
    assert ledger.get_latest(receipt.receipt_id) is not None


def test_orphan_decision_fails_causal_linkage_invariant():
    ledger = CABLedger()
    ledger.append(
        DecisionRecord(
            decision_id="cab.decision.orphan",
            decision_makers=["steward:x"],
            chosen_option="orphan",
            rationale="no intent",
            intent_refs=["cab.intent.missing"],
            created_at="2026-06-19T12:00:00Z",
        )
    )
    report = evaluate_cab_invariants(ledger)
    cl = next(item for item in report.results if item.invariant_id == "CL")
    assert cl.status == "fail"
