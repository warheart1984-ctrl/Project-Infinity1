"""Thin bridge into Foundation Law enforcement for evolve actions."""

from __future__ import annotations

from typing import Any

from evolve_engine.universal_language import enforce_foundation_laws


def enforce_laws(candidate: Any, action: str, context: dict[str, Any]) -> dict[str, Any]:
    return enforce_foundation_laws(
        artifact=candidate,
        action=action,
        context=context,
    )
