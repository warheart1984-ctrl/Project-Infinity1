"""FOS Architecture Registry."""

from __future__ import annotations

from src.fos.memory_core import MemoryCore
from src.fos.types import MemoryObject, MemoryType


class ArchitectureRegistry:
    ARCHITECTURE_TYPES = frozenset({MemoryType.ARCHITECTURE, MemoryType.SYSTEM_MODEL, MemoryType.BLUEPRINT})

    def __init__(self, memory: MemoryCore) -> None:
        self.memory = memory

    def register(self, obj: MemoryObject) -> None:
        if obj.mtype not in self.ARCHITECTURE_TYPES:
            raise ValueError(f"not an architecture object: {obj.mtype}")
        self.memory.upsert(obj)

    def list_all(self) -> list[MemoryObject]:
        return [obj for obj in self.memory.all() if obj.mtype in self.ARCHITECTURE_TYPES]

    def get(self, object_id: str) -> MemoryObject | None:
        obj = self.memory.get(object_id)
        if obj is None or obj.mtype not in self.ARCHITECTURE_TYPES:
            return None
        return obj
