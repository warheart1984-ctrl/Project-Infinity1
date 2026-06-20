"""FOS Kernel — minimal continuity substrate + projections."""

from __future__ import annotations

from typing import Any

from src.fos.architecture_registry import ArchitectureRegistry
from src.fos.blueprint import BlueprintCompiler, BlueprintKind
from src.fos.continuity import ContinuityEngine
from src.fos.decision_ledger import DecisionLedger
from src.fos.governance_registry import GovernanceRegistry
from src.fos.memory_core import MemoryCore
from src.fos.projections import ContinuityThreadExplorer, FounderMemoryVault, LineageGraph
from src.fos.reconstruction import ReconstructionEngine
from src.fos.translation import RawConversation, TranslationEngine
from src.fos.validation import ValidationLayer


class FosKernel:
    """Kernel = ContinuityEngine; everything else is a projection."""

    def __init__(
        self,
        continuity: ContinuityEngine | None = None,
        memory: MemoryCore | None = None,
    ) -> None:
        self.continuity = continuity or ContinuityEngine()
        self.memory = memory or MemoryCore(continuity=self.continuity)
        self.architecture = ArchitectureRegistry(self.memory)
        self.governance = GovernanceRegistry(self.memory)
        self.decisions = DecisionLedger(self.memory, continuity=self.continuity)
        self.vault = FounderMemoryVault(self.continuity)
        self.lineage_graph = LineageGraph(self.continuity)
        self.explorer = ContinuityThreadExplorer(self.continuity)
        self.reconstruction = ReconstructionEngine(self.continuity)

    def create_thread(self, thread_id: str, *, parent_thread_id: str | None = None) -> dict[str, Any]:
        return self.continuity.create_thread(thread_id, parent_thread_id=parent_thread_id).to_dict()

    def ingest_conversation(self, conv: RawConversation) -> list[str]:
        self.continuity.create_thread(conv.continuity_thread)
        ingested: list[str] = []
        for obj in TranslationEngine.conversation_to_memory(conv):
            if ValidationLayer.validate_memory(obj):
                self.memory.upsert(obj)
                ingested.append(obj.id)
        return ingested

    def compile_architecture_blueprint(self, thread: str) -> dict[str, Any]:
        sources = BlueprintCompiler.select_architecture_sources(self.memory.all())
        blueprint = BlueprintCompiler.from_memory(thread, sources, BlueprintKind.ARCHITECTURE)
        event = self.continuity.append_event(
            thread,
            "Blueprint",
            blueprint.to_dict(),
            lineage=[source.id for source in sources],
        )
        return event.to_dict()

    def compile_governance_blueprint(self, thread: str) -> dict[str, Any]:
        sources = BlueprintCompiler.select_governance_sources(self.memory.all())
        blueprint = BlueprintCompiler.from_memory(thread, sources, BlueprintKind.GOVERNANCE)
        event = self.continuity.append_event(
            thread,
            "Blueprint",
            blueprint.to_dict(),
            lineage=[source.id for source in sources],
        )
        return event.to_dict()

    def reconstruct_decision(self, event_id: str) -> dict[str, Any]:
        return self.reconstruction.reconstruct(event_id)

    def explore_thread(self, thread_id: str) -> dict[str, Any]:
        return self.explorer.explore(thread_id)

    def build_lineage_graph(self) -> dict[str, Any]:
        return self.lineage_graph.build()
