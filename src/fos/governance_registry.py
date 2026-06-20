"""FOS Governance Registry."""

from __future__ import annotations

from src.fos.memory_core import MemoryCore
from src.fos.types import MemoryObject, MemoryType


class GovernanceRegistry:
    GOVERNANCE_TYPES = frozenset({MemoryType.GOVERNANCE_CONTRACT, MemoryType.INVARIANT})

    def __init__(self, memory: MemoryCore) -> None:
        self.memory = memory

    def register(self, obj: MemoryObject) -> None:
        if obj.mtype not in self.GOVERNANCE_TYPES:
            raise ValueError(f"not a governance object: {obj.mtype}")
        self.memory.upsert(obj)

    def list_all(self) -> list[MemoryObject]:
        return [obj for obj in self.memory.all() if obj.mtype in self.GOVERNANCE_TYPES]

    def invariants(self) -> list[MemoryObject]:
        return [obj for obj in self.memory.all() if obj.mtype == MemoryType.INVARIANT]
