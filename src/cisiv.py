"""Shared CISIV stage helpers for AAIS operating surfaces."""

from __future__ import annotations


CISIV_STAGE_SEQUENCE = [
    "concept",
    "identity",
    "structure",
    "implementation",
    "verification",
]

CISIV_STAGE_LABELS = {
    "concept": "Concept",
    "identity": "Identity",
    "structure": "Structure",
    "implementation": "Implementation",
    "verification": "Verification",
}


def normalize_cisiv_stage(value: str | None, *, default: str = "implementation") -> str:
    """Return a canonical CISIV stage name with a safe fallback."""
    normalized_default = str(default or "implementation").strip().lower().replace("-", "_")
    if normalized_default not in CISIV_STAGE_LABELS:
        normalized_default = "implementation"

    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in CISIV_STAGE_LABELS:
        return normalized
    return normalized_default


def cisiv_stage_label(value: str | None, *, default: str = "implementation") -> str:
    stage = normalize_cisiv_stage(value, default=default)
    return CISIV_STAGE_LABELS[stage]
