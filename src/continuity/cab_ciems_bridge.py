"""CIEMS (Mutation Engine) → CAB DecisionRecord bridge."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from src.continuity.cab import CABLedger, DecisionRecord, default_cab_store_path

if TYPE_CHECKING:
    from src.governance_organs.mutation_engine import MutationProposal, MutationResult


def ciems_auto_link_enabled() -> bool:
    return os.environ.get("CAB_CIEMS_AUTO_LINK", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def ciems_intent_ref() -> str | None:
    value = os.environ.get("CAB_CIEMS_INTENT_ID", "").strip()
    return value or None


def decision_id_for_mutation(gene: str, mp_id: str) -> str:
    safe_mp = mp_id.replace(" ", "-")
    return f"cab.decision.ciems.{gene}.{safe_mp}"


def evidence_chain_ref_for_mutation(gene: str, mp_id: str) -> str:
    safe_mp = mp_id.replace(" ", "-")
    return f"cab.evidence.ciems.{gene}.{safe_mp}"


def record_mutation_decision(
    proposal: MutationProposal,
    result: MutationResult,
    *,
    intent_ref: str | None = None,
    ledger: CABLedger | None = None,
) -> DecisionRecord:
    """Map a successful CIEMS mutation apply into a CAB DecisionRecord."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    decision_id = decision_id_for_mutation(proposal.gene, proposal.mp_id)
    evidence_ref = evidence_chain_ref_for_mutation(proposal.gene, proposal.mp_id)
    delta_ref = proposal.operator_lanes_delta_ref or proposal.schema_delta_ref or ""
    rationale_parts = [
        f"CIEMS mutation {proposal.mp_id} applied to gene {proposal.gene}.",
        f"backward_compatible={proposal.backward_compatible}",
    ]
    if delta_ref:
        rationale_parts.append(f"delta_ref={delta_ref}")
    if proposal.mutation_kind:
        rationale_parts.append(f"mutation_kind={proposal.mutation_kind}")
    if result.failures:
        rationale_parts.append(f"verify_failures={result.failures}")

    intent_refs: list[str] = []
    resolved_intent = intent_ref or ciems_intent_ref()
    if resolved_intent:
        intent_refs.append(resolved_intent)

    decision = DecisionRecord(
        decision_id=decision_id,
        decision_makers=["ciems:mutation-engine"],
        intent_refs=intent_refs,
        options_considered=[
            {
                "option_id": "reject",
                "label": "Do not apply mutation",
                "pros": ["Preserves current genome"],
                "cons": ["Blocks schema evolution"],
            },
            {
                "option_id": "apply",
                "label": f"Apply {proposal.mp_id}",
                "pros": ["Promotes governed schema change"],
                "cons": ["Requires rollback path on failure"],
            },
        ],
        chosen_option="apply" if result.passed else "reject",
        rationale=" ".join(rationale_parts),
        govern_policy_refs=[
            "docs/_future/mutations/" + proposal.mp_id + ".md",
        ],
        evidence_chain_refs=[evidence_ref],
        review_conditions=f"Revisit on rollback of {proposal.mp_id}",
        created_at=now,
    )
    active = ledger or CABLedger.open(default_cab_store_path())
    if active.get_latest(decision_id) is None:
        active.append(decision)
    return decision


def maybe_link_mutation_decision(
    proposal: MutationProposal,
    result: MutationResult,
    *,
    ledger: CABLedger | None = None,
) -> DecisionRecord | None:
    """Append CAB DecisionRecord when auto-link is enabled and apply succeeded."""
    if not ciems_auto_link_enabled() or not result.passed:
        return None
    return record_mutation_decision(proposal, result, ledger=ledger)
