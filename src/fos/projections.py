"""Projections above the minimal kernel — vault, graph, explorer (Steps 4–5)."""

from __future__ import annotations

from typing import Any

from src.fos.continuity import ContinuityEngine
from src.fos.primitives import EventType, Id, ThreadId

VAULT_EVENT_TYPES = frozenset(
    {
        EventType.CONCEPT.value,
        EventType.ARCHITECTURE.value,
        EventType.GOVERNANCE.value,
        EventType.DECISION.value,
        EventType.EVIDENCE.value,
        "Invariant",
        "GovernanceContract",
        "Pattern",
        "SystemModel",
        "Blueprint",
        "FieldDefinition",
    }
)

CHAIN_ORDER = (
    EventType.DECISION.value,
    EventType.ARCHITECTURE.value,
    EventType.GOVERNANCE.value,
    EventType.EVIDENCE.value,
    EventType.CONCEPT.value,
)


class FounderMemoryVault:
    """Filtered view of continuity events — versioned continuity artifacts."""

    def __init__(self, continuity: ContinuityEngine) -> None:
        self.continuity = continuity

    def list_events(
        self,
        *,
        thread_id: ThreadId | None = None,
        event_types: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        types = event_types or set(VAULT_EVENT_TYPES)
        if thread_id:
            events = self.continuity.query_thread(thread_id)
        else:
            events = list(self.continuity.events.values())
        return [event.to_dict() for event in events if event.event_type in types]


class LineageGraph:
    """Persistent map of event connections via lineage pointers."""

    def __init__(self, continuity: ContinuityEngine) -> None:
        self.continuity = continuity

    def build(self) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, str]] = []
        for event in self.continuity.events.values():
            nodes.append(
                {
                    "id": event.event_id,
                    "thread_id": event.thread_id,
                    "type": event.event_type,
                    "timestamp": event.timestamp,
                }
            )
            for pointer in self.continuity.lineage_pointers(event.event_id):
                edges.append(pointer.to_dict())
        thread_edges: list[dict[str, str]] = []
        for thread in self.continuity.threads.values():
            if thread.parent_thread_id:
                thread_edges.append(
                    {
                        "from_thread_id": thread.thread_id,
                        "to_thread_id": thread.parent_thread_id,
                        "kind": "parent_thread",
                    }
                )
        return {
            "nodes": nodes,
            "edges": edges,
            "thread_edges": thread_edges,
        }


class ContinuityThreadExplorer:
    """UI/query layer: Decision → Architecture → Governance → Evidence → Outcome."""

    def __init__(self, continuity: ContinuityEngine) -> None:
        self.continuity = continuity

    def explore(self, thread_id: ThreadId) -> dict[str, Any]:
        events = self.continuity.query_thread(thread_id)
        by_type: dict[str, list[dict[str, Any]]] = {key: [] for key in CHAIN_ORDER}
        for event in events:
            bucket = by_type.get(event.event_type)
            if bucket is not None:
                bucket.append(event.to_dict())
            else:
                by_type.setdefault(event.event_type, []).append(event.to_dict())

        chain: list[dict[str, Any]] = []
        for event_type in CHAIN_ORDER:
            for item in by_type.get(event_type, []):
                chain.append({"stage": event_type, "event": item})

        return {
            "thread_id": thread_id,
            "event_count": len(events),
            "chain": chain,
            "by_type": by_type,
        }
