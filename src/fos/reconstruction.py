"""Decision Reconstruction Engine (Step 3) — why did we choose this?"""

from __future__ import annotations

from typing import Any

from src.fos.continuity import ContinuityEngine
from src.fos.primitives import ContinuityEvent, EventType, Id


class ReconstructionEngine:
    """Reconstruct discussion, decision, evidence, alternatives, outcome from lineage."""

    def __init__(self, continuity: ContinuityEngine) -> None:
        self.continuity = continuity

    def reconstruct(self, event_id: Id) -> dict[str, Any]:
        event = self.continuity.get_event(event_id)
        if event is None:
            raise ValueError(f"unknown event: {event_id}")

        lineage_chain = self.continuity.query_lineage(event_id)
        lineage_ids = [item.event_id for item in lineage_chain]

        concepts = [
            item for item in lineage_chain if item.event_type == EventType.CONCEPT.value
        ]
        architectures = [
            item for item in lineage_chain if item.event_type == EventType.ARCHITECTURE.value
        ]
        governance = [
            item for item in lineage_chain if item.event_type == EventType.GOVERNANCE.value
        ]
        evidence = [
            item for item in lineage_chain if item.event_type == EventType.EVIDENCE.value
        ]
        decisions = [
            item for item in lineage_chain if item.event_type == EventType.DECISION.value
        ]

        payload = dict(event.payload)
        return {
            "event_id": event.event_id,
            "thread_id": event.thread_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp,
            "lineage": lineage_ids,
            "rationale": payload.get("rationale") or payload.get("definition") or "",
            "chosen_option": payload.get("chosen_option"),
            "alternatives": payload.get("alternatives") or payload.get("options_considered") or [],
            "evidence_refs": payload.get("evidence_refs") or [],
            "outcome": payload.get("outcome"),
            "discussion": [self._summarize(item) for item in concepts],
            "architecture_context": [self._summarize(item) for item in architectures],
            "governance_context": [self._summarize(item) for item in governance],
            "evidence_context": [self._summarize(item) for item in evidence],
            "prior_decisions": [self._summarize(item) for item in decisions if item.event_id != event_id],
        }

    @staticmethod
    def _summarize(event: ContinuityEvent) -> dict[str, Any]:
        return {
            "event_id": event.event_id,
            "type": event.event_type,
            "timestamp": event.timestamp,
            "summary": event.payload.get("definition")
            or event.payload.get("rationale")
            or event.payload.get("event_description")
            or str(event.payload)[:200],
        }
