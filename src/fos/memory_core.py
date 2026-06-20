"""FOS Founder Memory Core — projection layer over ContinuityEngine."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.fos.continuity import ContinuityEngine
from src.fos.types import ContinuityThreadId, Id, MemoryObject


def default_fos_store_path() -> Path:
    override = os.environ.get("FOS_STORE", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    runtime = os.environ.get("AAIS_RUNTIME_DIR", "").strip()
    if runtime:
        return Path(runtime).expanduser().resolve() / "fos" / "memory.jsonl"
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".").expanduser()
    return home / ".fos" / "memory.jsonl"


class MemoryCore:
    """Memory vault projection — persists MemoryObject and mirrors as continuity events."""

    def __init__(
        self,
        store_path: Path | None = None,
        continuity: ContinuityEngine | None = None,
    ) -> None:
        self.store_path = store_path or default_fos_store_path()
        self.continuity = continuity or ContinuityEngine()
        self.objects: dict[Id, MemoryObject] = {}
        if self.store_path.exists():
            self._load()

    def upsert(self, obj: MemoryObject) -> None:
        self.objects[obj.id] = obj
        self._persist(obj)
        self.continuity.create_thread(obj.continuity_thread)
        if self.continuity.get_event(obj.id) is None:
            self.continuity.append_event(
                obj.continuity_thread,
                obj.mtype.value,
                obj.to_dict(),
                lineage=list(obj.lineage),
                event_id=obj.id,
            )

    def get(self, object_id: Id) -> MemoryObject | None:
        return self.objects.get(object_id)

    def all(self) -> list[MemoryObject]:
        return list(self.objects.values())

    def by_thread(self, thread: ContinuityThreadId) -> list[MemoryObject]:
        return [obj for obj in self.objects.values() if obj.continuity_thread == thread]

    def _persist(self, obj: MemoryObject) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(obj.to_dict(), sort_keys=True) + "\n")

    def _load(self) -> None:
        for line in self.store_path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            obj = MemoryObject.from_dict(json.loads(cleaned))
            self.objects[obj.id] = obj
