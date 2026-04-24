"""AAIS Universal Language adaptation layer.

This module turns raw modular context, provider previews, and guardrail state
into one shared UL payload shape so Jarvis can inspect what entered the system
before provider delivery.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


SECTION_BY_CHANNEL = {
    "instruction": "identity",
    "runtime": "runtime_context",
    "memory": "knowledge_context",
    "workspace": "workspace_context",
    "research": "knowledge_context",
    "corrigibility": "guardrail_state",
    "browser": "protocol_trace",
    "specialist": "knowledge_context",
    "orchestration": "mission_context",
    "tool": "tool_results",
}


@dataclass(slots=True)
class ULPayload:
    source: str
    kind: str
    section: str
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "kind": self.kind,
            "section": self.section,
            "data": dict(self.data),
            "metadata": dict(self.metadata),
        }


class ULAdapter(ABC):
    name = "ul_adapter"

    @abstractmethod
    def supports(self, raw: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    def adapt(self, raw: Any) -> ULPayload:
        raise NotImplementedError


class ULRegistry:
    def __init__(self) -> None:
        self.adapters: list[ULAdapter] = []

    def register(self, adapter: ULAdapter) -> None:
        self.adapters.append(adapter)

    def adapt(self, raw: Any) -> ULPayload:
        for adapter in self.adapters:
            if adapter.supports(raw):
                return adapter.adapt(raw)
        raise ValueError("No UL adapter found for payload.")

    def try_adapt(self, raw: Any) -> ULPayload | None:
        for adapter in self.adapters:
            if adapter.supports(raw):
                return adapter.adapt(raw)
        return None


class RuntimeContextAdapter(ULAdapter):
    name = "runtime_context_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "runtime_context"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="context",
            section="runtime_context",
            data={
                "environment": raw.get("environment"),
                "provider": raw.get("provider"),
                "mode": raw.get("mode"),
            },
            metadata={"raw_type": raw.get("type")},
        )


class WorkspaceRunnerAdapter(ULAdapter):
    name = "workspace_runner_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "workspace_runner"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="workspace",
            section="workspace_context",
            data={
                "status": raw.get("status"),
                "active_task": raw.get("active_task"),
                "artifacts": raw.get("artifacts", []),
                "steps": raw.get("steps", []),
            },
            metadata={"raw_type": raw.get("type")},
        )


class ToolResultAdapter(ULAdapter):
    name = "tool_result_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "tool_result"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="tool_result",
            section="tool_results",
            data={
                "tool": raw.get("tool"),
                "status": raw.get("status"),
                "result": raw.get("result"),
            },
            metadata={"raw_type": raw.get("type")},
        )


class AttachmentAdapter(ULAdapter):
    name = "attachment_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "attachment"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="attachment",
            section="attachments",
            data={
                "name": raw.get("name"),
                "mime_type": raw.get("mime_type"),
                "size": raw.get("size"),
            },
            metadata={"raw_type": raw.get("type")},
        )


class ProtocolModuleAdapter(ULAdapter):
    name = "protocol_module_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and "channel" in raw and "content" in raw

    def adapt(self, raw: Any) -> ULPayload:
        channel = str(raw.get("channel") or "instruction").strip().lower()
        return ULPayload(
            source=str(raw.get("source_module") or self.name),
            kind="module",
            section=SECTION_BY_CHANNEL.get(channel, "protocol_trace"),
            data={
                "channel": channel,
                "label": raw.get("label"),
                "content": raw.get("content"),
                "role": raw.get("role"),
            },
            metadata=dict(raw.get("metadata") or {}),
        )


class ProviderPreviewAdapter(ULAdapter):
    name = "provider_preview_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and "messages" in raw and "model" in raw

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="preview",
            section="provider_payload",
            data={
                "model": raw.get("model"),
                "message_count": len(raw.get("messages") or []),
                "mode": raw.get("mode"),
                "stream": bool(raw.get("stream")),
            },
            metadata=dict(raw.get("metadata") or {}),
        )


class GuardrailStateAdapter(ULAdapter):
    name = "guardrail_state_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "status" in raw
            and "protected_zones" in raw
            and "effective_pipeline" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="guardrail",
            section="guardrail_state",
            data={
                "status": raw.get("status"),
                "summary": raw.get("summary"),
                "pipeline_mode": raw.get("pipeline_mode"),
                "effective_pipeline": list(raw.get("effective_pipeline") or []),
                "requested_pipeline": list(raw.get("requested_pipeline") or []),
                "adaptive_zone": raw.get("adaptive_zone"),
                "override_blocked": bool(raw.get("override_blocked")),
            },
            metadata={
                "protected_zones": list(raw.get("protected_zones") or []),
                "allowed_growth_zones": list(raw.get("allowed_growth_zones") or []),
            },
        )


def build_default_registry() -> ULRegistry:
    registry = ULRegistry()
    registry.register(RuntimeContextAdapter())
    registry.register(WorkspaceRunnerAdapter())
    registry.register(ToolResultAdapter())
    registry.register(AttachmentAdapter())
    registry.register(ProtocolModuleAdapter())
    registry.register(ProviderPreviewAdapter())
    registry.register(GuardrailStateAdapter())
    return registry


DEFAULT_REGISTRY = build_default_registry()


def build_ul_snapshot(
    *,
    modules: list[dict[str, Any]] | None = None,
    provider_preview: dict[str, Any] | None = None,
    guardrail_state: dict[str, Any] | None = None,
    registry: ULRegistry | None = None,
) -> dict[str, Any]:
    """Adapt the active modular turn into inspectable UL payloads."""
    active_registry = registry or DEFAULT_REGISTRY
    payloads: list[dict[str, Any]] = []

    for module in modules or []:
        payload = active_registry.try_adapt(module)
        if payload:
            payloads.append(payload.to_dict())

    preview_payload = active_registry.try_adapt(provider_preview or {})
    if preview_payload:
        payloads.append(preview_payload.to_dict())

    guardrail_payload = active_registry.try_adapt(guardrail_state or {})
    if guardrail_payload:
        payloads.append(guardrail_payload.to_dict())

    sections: list[str] = []
    for payload in payloads:
        section = payload.get("section")
        if section and section not in sections:
            sections.append(section)

    return {
        "count": len(payloads),
        "sections": sections,
        "payloads": payloads,
    }
