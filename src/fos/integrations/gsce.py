"""GSCE ↔ FOS validation hooks."""

from __future__ import annotations

from src.fos.types import MemoryObject
from src.fos.validation import ValidationLayer


def gsce_validate_memory(obj: MemoryObject) -> dict:
    """GSCE defines rules; FOS validation layer enforces them."""
    ok, failures = ValidationLayer.validate_memory_strict(obj)
    return {"passed": ok, "failures": failures, "rule_source": "gsce:fos-v0.1"}
