"""FOS Kernel — founder cognition pipeline orchestrator."""

from __future__ import annotations

from typing import Any

from src.fos.architecture_registry import ArchitectureRegistry
from src.fos.blueprint import BlueprintCompiler, BlueprintKind
from src.fos.continuity import ContinuityEngine
from src.fos.decision_ledger import DecisionLedger
from src.fos.governance_registry import GovernanceRegistry
from src.fos.memory_core import MemoryCore
from src.fos.translation import RawConversation, TranslationEngine
from src.fos.validation import ValidationLayer


class FosKernel:
    def __init__(self, memory: MemoryCore | None = None) -> None:
        self.memory = memory or MemoryCore()
        self.architecture = ArchitectureRegistry(self.memory)
        self.governance = GovernanceRegistry(self.memory)
        self.decisions = DecisionLedger(self.memory)
        self.events: list[dict[str, Any]] = []

    def ingest_conversation(self, conv: RawConversation) -> list[str]:
        ingested: list[str] = []
        for obj in TranslationEngine.conversation_to_memory(conv):
            if ValidationLayer.validate_memory(obj):
                self.memory.upsert(obj)
                ingested.append(obj.id)
                event = ContinuityEngine.emit(
                    "memory:ingest",
                    conv.continuity_thread,
                    {"memory_id": obj.id, "mtype": obj.mtype.value},
                )
                self.events.append(event.to_dict())
        return ingested

    def compile_architecture_blueprint(self, thread: str) -> dict[str, Any]:
        sources = BlueprintCompiler.select_architecture_sources(self.memory.all())
        blueprint = BlueprintCompiler.from_memory(thread, sources, BlueprintKind.ARCHITECTURE)
        event = ContinuityEngine.emit(
            "blueprint:architecture",
            blueprint.continuity_thread,
            blueprint.to_dict(),
        )
        self.events.append(event.to_dict())
        return event.to_dict()

    def compile_governance_blueprint(self, thread: str) -> dict[str, Any]:
        sources = BlueprintCompiler.select_governance_sources(self.memory.all())
        blueprint = BlueprintCompiler.from_memory(thread, sources, BlueprintKind.GOVERNANCE)
        event = ContinuityEngine.emit(
            "blueprint:governance",
            blueprint.continuity_thread,
            blueprint.to_dict(),
        )
        self.events.append(event.to_dict())
        return event.to_dict()
