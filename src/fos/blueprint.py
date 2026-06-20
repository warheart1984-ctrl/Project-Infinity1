"""FOS Blueprint Compiler."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import uuid4

from src.fos.types import ContinuityThreadId, Id, MemoryObject, MemoryType, Version


class BlueprintKind(str, Enum):
    ARCHITECTURE = "Architecture"
    GOVERNANCE = "Governance"


@dataclass
class Blueprint:
    id: Id
    source_ids: list[Id]
    kind: BlueprintKind
    content: dict[str, Any]
    version: Version
    continuity_thread: ContinuityThreadId

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_ids": list(self.source_ids),
            "kind": self.kind.value,
            "content": dict(self.content),
            "version": self.version,
            "continuity_thread": self.continuity_thread,
        }


class BlueprintCompiler:
    @staticmethod
    def from_memory(
        continuity_thread: ContinuityThreadId,
        sources: list[MemoryObject],
        kind: BlueprintKind,
    ) -> Blueprint:
        source_ids = [obj.id for obj in sources]
        content = {
            "sources": source_ids,
            "kind": kind.value,
        }
        return Blueprint(
            id=f"bp-{uuid4()}",
            source_ids=source_ids,
            kind=kind,
            content=content,
            version=Version("v0.1.0"),
            continuity_thread=continuity_thread,
        )

    @staticmethod
    def select_architecture_sources(objects: list[MemoryObject]) -> list[MemoryObject]:
        return [
            obj
            for obj in objects
            if obj.mtype in {MemoryType.ARCHITECTURE, MemoryType.SYSTEM_MODEL}
        ]

    @staticmethod
    def select_governance_sources(objects: list[MemoryObject]) -> list[MemoryObject]:
        return [
            obj
            for obj in objects
            if obj.mtype in {MemoryType.GOVERNANCE_CONTRACT, MemoryType.INVARIANT}
        ]
