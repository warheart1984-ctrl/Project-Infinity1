"""FOS Validation Layer — memory integrity rules."""

from __future__ import annotations

from src.fos.types import MemoryObject


class ValidationLayer:
    @staticmethod
    def validate_memory(obj: MemoryObject) -> bool:
        return (
            bool(obj.definition.strip())
            and bool(obj.version.strip())
            and bool(obj.continuity_thread.strip())
            and bool(obj.mtype)
        )

    @staticmethod
    def validate_memory_strict(obj: MemoryObject) -> tuple[bool, list[str]]:
        failures: list[str] = []
        if not obj.definition.strip():
            failures.append("definition required")
        if not obj.version.strip():
            failures.append("version required")
        if not obj.continuity_thread.strip():
            failures.append("continuity_thread required")
        if not obj.mtype:
            failures.append("type required")
        if not obj.lineage:
            failures.append("lineage required")
        return (not failures, failures)
