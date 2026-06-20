"""DAR-Z ↔ FOS integration contract."""

from __future__ import annotations

from src.fos.kernel import FosKernel
from src.fos.types import MemoryObject, MemoryType


def export_concepts_for_darz(kernel: FosKernel, *, thread: str) -> list[dict]:
    """DAR-Z consumes concepts, invariants, architectures from FOS."""
    return [
        obj.to_dict()
        for obj in kernel.memory.by_thread(thread)
        if obj.mtype in {MemoryType.CONCEPT, MemoryType.INVARIANT, MemoryType.ARCHITECTURE}
    ]


def ingest_darz_trace(kernel: FosKernel, *, trace_id: str, assumptions: list[str], thread: str) -> MemoryObject:
    """DAR-Z produces reasoning traces → FOS memory."""
    obj = MemoryObject(
        id=f"mem-darz-{trace_id}",
        mtype=MemoryType.EVIDENCE,
        definition=f"DAR-Z trace {trace_id}",
        evidence_refs=[trace_id],
        lineage=assumptions,
        continuity_thread=thread,
    )
    kernel.memory.upsert(obj)
    return obj
