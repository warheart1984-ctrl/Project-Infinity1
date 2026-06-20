"""FOS core types — mirror fos-kernel Rust ontology."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

Id = str
Version = str
ContinuityThreadId = str
EvidenceRef = str


class MemoryType(str, Enum):
    CONCEPT = "Concept"
    PATTERN = "Pattern"
    INVARIANT = "Invariant"
    ARCHITECTURE = "Architecture"
    GOVERNANCE_CONTRACT = "GovernanceContract"
    DECISION = "Decision"
    EVIDENCE = "Evidence"
    CONTINUITY_THREAD = "ContinuityThread"
    SYSTEM_MODEL = "SystemModel"
    BLUEPRINT = "Blueprint"
    FIELD_DEFINITION = "FieldDefinition"


@dataclass
class MemoryObject:
    id: Id
    mtype: MemoryType
    definition: str
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    lineage: list[Id] = field(default_factory=list)
    version: Version = "v0.1.0"
    continuity_thread: ContinuityThreadId = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "mtype": self.mtype.value,
            "definition": self.definition,
            "evidence_refs": list(self.evidence_refs),
            "lineage": list(self.lineage),
            "version": self.version,
            "continuity_thread": self.continuity_thread,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> MemoryObject:
        return cls(
            id=str(raw["id"]),
            mtype=MemoryType(str(raw["mtype"])),
            definition=str(raw.get("definition") or ""),
            evidence_refs=[str(item) for item in (raw.get("evidence_refs") or [])],
            lineage=[str(item) for item in (raw.get("lineage") or [])],
            version=str(raw.get("version") or "v0.1.0"),
            continuity_thread=str(raw.get("continuity_thread") or ""),
        )
