"""Replay thread events in causal order and compute ThreadProof."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.aais.reconstruction.types import REPLAY_KINDS, ContinuityEvent, LineageGraph, ThreadProof


@dataclass
class ReplayState:
    known_evidence: set[str] = field(default_factory=set)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    superseded_decisions: set[str] = field(default_factory=set)
    last_event_id: str | None = None


def _finding(kind: str, code: str, message: str, event_ids: list[str]) -> dict[str, Any]:
    return {"kind": kind, "code": code, "message": message, "event_ids": event_ids}


def _decision_backed(
    event: ContinuityEvent,
    state: ReplayState,
    graph: LineageGraph,
    *,
    all_events: dict[str, ContinuityEvent] | None = None,
) -> bool:
    events_index = all_events if all_events is not None else graph.events
    refs = {str(item) for item in (event.payload.get("evidence_refs") or [])}
    lineage_evidence = {
        parent_id
        for parent_id in event.causal_lineage
        if parent_id in events_index and events_index[parent_id].kind == "Evidence"
    }
    candidates = refs | lineage_evidence
    if not candidates:
        return False
    return all(
        ref in events_index
        and (
            ref in state.known_evidence
            or events_index[ref].kind == "Evidence"
        )
        for ref in candidates
    )


def replay_thread(
    graph: LineageGraph,
    *,
    all_events: dict[str, ContinuityEvent] | None = None,
) -> ThreadProof:
    events_index = all_events if all_events is not None else graph.events
    state = ReplayState()
    findings: list[dict[str, Any]] = []
    replayed = 0
    decision_count = 0
    evidence_count = 0

    ordered = graph.ordered_events()
    for event in ordered:
        if event.kind not in REPLAY_KINDS:
            continue
        replayed += 1
        state.last_event_id = event.event_id

        if event.kind == "Evidence":
            state.known_evidence.add(event.event_id)
            evidence_count += 1
        elif event.kind == "Decision":
            decision_count += 1
            backed = _decision_backed(event, state, graph, all_events=events_index)
            state.decisions.append(
                {
                    "event_id": event.event_id,
                    "backed": backed,
                    "superseded": event.event_id in state.superseded_decisions,
                }
            )
            if not backed:
                findings.append(
                    _finding(
                        "Error",
                        "UNBACKED_DECISION",
                        f"Decision {event.event_id} lacks backing evidence",
                        [event.event_id],
                    )
                )
        elif event.kind == "Correction":
            target = event.payload.get("corrects_event_id") or event.payload.get("decision_ref")
            if target:
                state.superseded_decisions.add(str(target))
        elif event.kind == "Override":
            target = event.payload.get("acknowledged_decision_id") or event.payload.get("decision_ref")
            if not target or str(target) not in graph.events:
                findings.append(
                    _finding(
                        "Warning",
                        "UNACKNOWLEDGED_OVERRIDE",
                        f"Override {event.event_id} lacks acknowledged decision",
                        [event.event_id],
                    )
                )
            elif target:
                state.superseded_decisions.add(str(target))
        elif event.kind == "Error":
            findings.append(
                _finding(
                    "Error",
                    "REPLAY_ERROR",
                    str(event.payload.get("message") or event.payload.get("summary") or "Error recorded"),
                    [event.event_id],
                )
            )

    for broken in graph.broken_lineage:
        findings.append(
            _finding(
                "Error",
                "BROKEN_LINEAGE",
                f"Event {broken['event_id']} references missing parent {broken['missing_parent_id']}",
                [broken["event_id"], broken["missing_parent_id"]],
            )
        )

    for orphan_id in graph.orphans:
        findings.append(
            _finding(
                "Warning",
                "ORPHANED_EVENT",
                f"Event {orphan_id} is structurally orphaned",
                [orphan_id],
            )
        )

    for cycle in graph.cycles:
        findings.append(
            _finding(
                "Error",
                "LINEAGE_CYCLE",
                "Cycle detected in causal lineage",
                cycle,
            )
        )

    no_broken = not graph.broken_lineage and not graph.cycles
    no_orphans = not graph.orphans
    unbacked = [item for item in state.decisions if not item["backed"]]
    no_unbacked = not unbacked

    invariants = {
        "no_orphaned_events": no_orphans,
        "no_broken_lineage": no_broken,
        "no_unbacked_decisions": no_unbacked,
    }

    first_event = ordered[0].event_id if ordered else None
    last_event = ordered[-1].event_id if ordered else None

    return ThreadProof(
        thread_id=graph.thread_id,
        events_replayed=replayed,
        lineage_ok=no_broken,
        evidence_ok=evidence_count > 0 or decision_count == 0,
        decisions_ok=no_unbacked,
        invariants=invariants,
        summary={
            "first_event": first_event,
            "last_event": last_event,
            "decision_count": decision_count,
            "evidence_count": evidence_count,
        },
        findings=findings,
    )
