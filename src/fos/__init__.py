"""Founder Operating System (FOS) v0.1 — institutional memory substrate."""

from src.fos.continuity import ContinuityEngine
from src.fos.kernel import FosKernel
from src.fos.primitives import ContinuityEvent, ContinuityThread, EventType, LineagePointer
from src.fos.projections import ContinuityThreadExplorer, FounderMemoryVault, LineageGraph
from src.fos.reconstruction import ReconstructionEngine
from src.fos.types import MemoryObject, MemoryType

__all__ = [
    "ContinuityEngine",
    "ContinuityEvent",
    "ContinuityThread",
    "ContinuityThreadExplorer",
    "EventType",
    "FosKernel",
    "FounderMemoryVault",
    "LineageGraph",
    "LineagePointer",
    "MemoryObject",
    "MemoryType",
    "ReconstructionEngine",
]
