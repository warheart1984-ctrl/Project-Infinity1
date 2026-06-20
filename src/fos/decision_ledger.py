"""FOS Decision Ledger with CAB sync hook."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.continuity.cab import CABLedger, DecisionRecord, default_cab_store_path
from src.fos.memory_core import MemoryCore
from src.fos.types import MemoryObject, MemoryType


@dataclass
class FosDecision:
    id: str
    rationale: str
    chosen_option: str
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)
    lineage: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    continuity_thread: str = ""
    version: str = "v0.1.0"
    intent_refs: list[str] = field(default_factory=list)

    def to_memory_object(self) -> MemoryObject:
        definition = f"{self.chosen_option}: {self.rationale}"
        return MemoryObject(
            id=self.id,
            mtype=MemoryType.DECISION,
            definition=definition,
            evidence_refs=list(self.evidence_refs),
            lineage=list(self.lineage),
            version=self.version,
            continuity_thread=self.continuity_thread,
        )


class DecisionLedger:
    def __init__(self, memory: MemoryCore) -> None:
        self.memory = memory
        self._decisions: dict[str, FosDecision] = {}

    def record(self, decision: FosDecision) -> MemoryObject:
        obj = decision.to_memory_object()
        self.memory.upsert(obj)
        self._decisions[decision.id] = decision
        return obj

    def sync_to_cab(
        self,
        decision: FosDecision,
        *,
        ledger: CABLedger | None = None,
    ) -> DecisionRecord:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        cab_id = decision.id if decision.id.startswith("cab.") else f"cab.decision.fos.{decision.id}"
        record = DecisionRecord(
            decision_id=cab_id,
            decision_makers=["fos:decision-ledger"],
            intent_refs=list(decision.intent_refs),
            options_considered=list(decision.alternatives),
            chosen_option=decision.chosen_option,
            rationale=decision.rationale,
            evidence_chain_refs=list(decision.evidence_refs),
            created_at=now,
        )
        active = ledger or CABLedger.open(default_cab_store_path())
        if active.get_latest(cab_id) is None:
            active.append(record)
        return record

    def get(self, decision_id: str) -> FosDecision | None:
        return self._decisions.get(decision_id)
