"""FOS Continuity Engine — minimal kernel runtime (Step 1)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.fos.primitives import ContinuityEvent, ContinuityThread, Id, LineagePointer, ThreadId


def default_continuity_store_path() -> Path:
    override = os.environ.get("FOS_CONTINUITY_STORE", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    base = os.environ.get("FOS_STORE", "").strip()
    if base:
        return Path(base).expanduser().resolve() / "continuity.jsonl"
    runtime = os.environ.get("AAIS_RUNTIME_DIR", "").strip()
    if runtime:
        return Path(runtime).expanduser().resolve() / "fos" / "continuity.jsonl"
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".").expanduser()
    return home / ".fos" / "continuity.jsonl"


class ContinuityEngine:
    """Kernel: create thread, append event, query thread, query lineage."""

    def __init__(self, store_path: Path | None = None) -> None:
        self.store_path = store_path or default_continuity_store_path()
        self.threads: dict[ThreadId, ContinuityThread] = {}
        self.events: dict[Id, ContinuityEvent] = {}
        if self.store_path.exists():
            self._load()

    def create_thread(
        self,
        thread_id: ThreadId,
        *,
        parent_thread_id: ThreadId | None = None,
    ) -> ContinuityThread:
        existing = self.threads.get(thread_id)
        if existing is not None:
            if parent_thread_id and not existing.parent_thread_id:
                existing.parent_thread_id = parent_thread_id
            return existing
        thread = ContinuityThread(
            thread_id=thread_id,
            parent_thread_id=parent_thread_id,
        )
        self.threads[thread_id] = thread
        self._persist_record({"record_type": "thread", **thread.to_dict()})
        return thread

    def append_event(
        self,
        thread_id: ThreadId,
        event_type: str,
        payload: dict[str, Any],
        *,
        lineage: list[Id] | None = None,
        event_id: Id | None = None,
        timestamp: str | None = None,
    ) -> ContinuityEvent:
        self.create_thread(thread_id)
        now = timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        resolved_id = event_id or f"evt-{uuid4()}"
        if resolved_id in self.events:
            raise ValueError(f"event already exists: {resolved_id}")
        event = ContinuityEvent(
            event_id=resolved_id,
            thread_id=thread_id,
            event_type=event_type,
            payload=dict(payload),
            timestamp=now,
            lineage=list(lineage or []),
        )
        self.events[resolved_id] = event
        thread = self.threads[thread_id]
        thread.event_ids.append(resolved_id)
        self._persist_record({"record_type": "event", **event.to_dict()})
        return event

    def get_event(self, event_id: Id) -> ContinuityEvent | None:
        return self.events.get(event_id)

    def get_thread(self, thread_id: ThreadId) -> ContinuityThread | None:
        return self.threads.get(thread_id)

    def query_thread(self, thread_id: ThreadId) -> list[ContinuityEvent]:
        thread = self.threads.get(thread_id)
        if thread is None:
            return []
        return [self.events[event_id] for event_id in thread.event_ids if event_id in self.events]

    def query_lineage(self, event_id: Id) -> list[ContinuityEvent]:
        """Walk lineage pointers backward from event to root."""
        chain: list[ContinuityEvent] = []
        current = self.events.get(event_id)
        if current is None:
            return chain
        chain.append(current)
        visited: set[Id] = {event_id}
        for parent_id in current.lineage:
            if parent_id in visited:
                continue
            parent = self.events.get(parent_id)
            if parent is None:
                continue
            chain.append(parent)
            visited.add(parent_id)
            for ancestor_id in parent.lineage:
                if ancestor_id in visited:
                    continue
                ancestor = self.events.get(ancestor_id)
                if ancestor is not None:
                    chain.append(ancestor)
                    visited.add(ancestor_id)
        return chain

    def lineage_pointers(self, event_id: Id) -> list[LineagePointer]:
        event = self.events.get(event_id)
        if event is None:
            return []
        return LineagePointer.from_lineage(event.event_id, event.lineage)

    def _persist_record(self, record: dict[str, Any]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def _load(self) -> None:
        for line in self.store_path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            record = json.loads(cleaned)
            record_type = record.get("record_type")
            if record_type == "thread":
                thread = ContinuityThread.from_dict(record)
                self.threads[thread.thread_id] = thread
            elif record_type == "event":
                event = ContinuityEvent.from_dict(record)
                self.events[event.event_id] = event
                thread = self.threads.setdefault(
                    event.thread_id,
                    ContinuityThread(thread_id=event.thread_id),
                )
                if event.event_id not in thread.event_ids:
                    thread.event_ids.append(event.event_id)
