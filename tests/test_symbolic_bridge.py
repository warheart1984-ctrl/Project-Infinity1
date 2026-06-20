"""Symbolic organism + FOS/CAB bridge tests."""

from __future__ import annotations

from src.continuity.cab import CABLedger
from src.fos.symbolic_bridge import ingest_symbolic_state
from src.symbolic_organism import GovernedSymbolicVM


def test_coherent_promotion_ingests_cab_and_fos():
    vm = GovernedSymbolicVM(
        decision_ids=("dec:cab-eval-branch-3",),
        evidence_refs=("ev:receipt:123",),
    )
    state = vm.evaluate("⟲?")
    ledger = CABLedger()
    result = ingest_symbolic_state(state, ledger=ledger)
    assert result["cab_receipt_ids"]
    assert result["fos_evidence_ids"]
    assert ledger.get_latest(result["cab_receipt_ids"][0]) is not None
