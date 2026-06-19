"""Jarvis-protocol adapter for the in-repo Lawful Nova runtime."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from src.jarvis_protocol import JarvisMessage, ProviderResponse


def _extract_prompt(messages: list[JarvisMessage | dict[str, Any]]) -> str:
    normalized = [
        message if isinstance(message, JarvisMessage) else JarvisMessage.from_dict(message)
        for message in messages or []
    ]
    for message in reversed(normalized):
        if str(message.role).strip().lower() == "user" and str(message.content or "").strip():
            return str(message.content).strip()
    if normalized:
        return str(normalized[-1].content or "").strip()
    return ""


def _map_capability(*, capability: str = "", response_mode: str = "", mode: str = "") -> str:
    explicit = str(capability or "").strip().lower()
    if explicit in {"observe", "reason", "summarize"}:
        return explicit
    response_mode = str(response_mode or mode or "observe").strip().lower()
    if response_mode in {"think", "reason", "deliberate"}:
        return "reason"
    if response_mode in {"summarize", "summary"}:
        return "summarize"
    return "observe"


class NovaLawfulProvider:
    """Route governed LLM execution through LawfulLLM (UGR + LSG + CVR receipts)."""

    def __init__(self, *, label: str = "Lawful Nova") -> None:
        self.label = label

    async def invoke(
        self,
        messages: list[JarvisMessage | dict[str, Any]],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> ProviderResponse:
        del tools

        from nova.runtime_factory import build_lawful_llm

        prompt = _extract_prompt(messages)
        if not prompt:
            return ProviderResponse(
                content="",
                provider="nova_lawful",
                model="lawful-nova",
                stop_reason="empty_prompt",
            )

        routing_profile = dict(kwargs.get("routing_profile") or {})
        tenant_id = str(
            routing_profile.get("tenant_id")
            or kwargs.get("tenant_id")
            or os.getenv("NOVA_DEFAULT_TENANT", "local")
        ).strip()
        capability = _map_capability(
            capability=str(
                kwargs.get("nova_capability")
                or kwargs.get("capability")
                or routing_profile.get("capability")
                or ""
            ),
            response_mode=str(kwargs.get("response_mode") or routing_profile.get("response_mode") or ""),
            mode=str(kwargs.get("mode") or routing_profile.get("mode") or ""),
        )
        operator_session = str(
            routing_profile.get("operator_session_id")
            or os.getenv("NOVA_OPERATOR_SESSION_ID", "urg-mission")
        ).strip()
        signing_secret = str(os.getenv("NOVA_SIGNING_SECRET", "local-dev-secret")).strip()

        llm = build_lawful_llm(
            operator_session_id=operator_session,
            signing_secret=signing_secret,
            tenant_id=tenant_id,
        )

        def _run_turn():
            return llm.ask(prompt, tenant_id=tenant_id, capability=capability)

        turn = await asyncio.to_thread(_run_turn)
        receipt = dict(turn.receipt or {})
        continuity = dict(turn.continuity_governance or {})
        metadata = {
            "lawful_turn": {
                "trace_id": receipt.get("trace_id"),
                "proof_id": (continuity.get("proof") or {}).get("proof_id"),
                "cvr_id": (continuity.get("cvr") or {}).get("cvr_id"),
                "voss_decision": (turn.voss_runtime or {}).get("decision"),
            }
        }

        return ProviderResponse(
            content=str(turn.text or "").strip(),
            provider="nova_lawful",
            model="lawful-nova",
            stop_reason="lawful_turn_complete",
            raw=metadata,
        )
