"""Build in-memory lineage graphs per thread."""

from __future__ import annotations

from collections import defaultdict

from src.aais.reconstruction.types import ContinuityEvent, LineageGraph


def _thread_ancestors(thread_id: str, thread_parents: dict[str, str | None]) -> set[str]:
    ancestors: set[str] = set()
    current = thread_parents.get(thread_id)
    while current:
        ancestors.add(current)
        current = thread_parents.get(current)
    return ancestors


def _detect_cycles(events: dict[str, ContinuityEvent]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def visit(event_id: str) -> None:
        if event_id in stack:
            if event_id in path:
                start = path.index(event_id)
                cycles.append(path[start:] + [event_id])
            return
        if event_id in visited:
            return
        visited.add(event_id)
        stack.add(event_id)
        path.append(event_id)
        event = events.get(event_id)
        if event is not None:
            for parent_id in event.causal_lineage:
                if parent_id in events:
                    visit(parent_id)
        path.pop()
        stack.remove(event_id)

    for event_id in events:
        visit(event_id)
    return cycles


def build_lineage_graphs(
    events: list[ContinuityEvent],
    *,
    thread_parents: dict[str, str | None] | None = None,
) -> dict[str, LineageGraph]:
    thread_parents = dict(thread_parents or {})
    all_events: dict[str, ContinuityEvent] = {event.event_id: event for event in events}
    by_thread: dict[str, dict[str, ContinuityEvent]] = defaultdict(dict)
    for event in events:
        by_thread[event.thread_id][event.event_id] = event
        if event.thread_id not in thread_parents:
            thread_parents[event.thread_id] = None

    graphs: dict[str, LineageGraph] = {}
    for thread_id, thread_events in by_thread.items():
        graph = LineageGraph(thread_id=thread_id, events=dict(thread_events))
        referenced: set[str] = set()
        broken: list[dict[str, str]] = []
        allowed_ancestor_threads = _thread_ancestors(thread_id, thread_parents)

        for event in thread_events.values():
            for parent_id in event.causal_lineage:
                referenced.add(parent_id)
                if parent_id in thread_events:
                    continue
                parent_event = all_events.get(parent_id)
                if parent_event is None:
                    broken.append(
                        {
                            "event_id": event.event_id,
                            "missing_parent_id": parent_id,
                            "thread_id": thread_id,
                        }
                    )
                    continue
                parent_thread = parent_event.thread_id
                if parent_thread == thread_id:
                    continue
                if parent_thread not in allowed_ancestor_threads:
                    # Peer cross-thread refs are valid when the event exists on the wire.
                    continue

        genesis_ids = {
            event_id
            for event_id, event in thread_events.items()
            if not event.causal_lineage and event.parent_event_id is None
        }
        if not genesis_ids and thread_events:
            earliest = min(thread_events.values(), key=lambda item: (item.timestamp, item.event_id))
            genesis_ids = {earliest.event_id}

        roots = sorted(
            event_id
            for event_id, event in thread_events.items()
            if not event.causal_lineage and event.parent_event_id is None
        )
        if not roots and thread_events:
            roots = [min(thread_events.values(), key=lambda item: (item.timestamp, item.event_id)).event_id]

        orphans = sorted(
            event_id
            for event_id, event in thread_events.items()
            if event_id not in genesis_ids
            and not event.causal_lineage
            and event.parent_event_id is None
        )

        graph.roots = roots
        graph.orphans = orphans
        graph.broken_lineage = broken
        graph.cycles = _detect_cycles(thread_events)
        graphs[thread_id] = graph
    return graphs
