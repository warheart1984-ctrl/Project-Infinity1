"""FOS Translation Engine — conversation to structured memory."""

from __future__ import annotations

from dataclasses import dataclass

from src.fos.types import MemoryObject, MemoryType, Version


@dataclass
class RawConversation:
    id: str
    text: str
    continuity_thread: str


class TranslationEngine:
    @staticmethod
    def conversation_to_memory(conv: RawConversation) -> list[MemoryObject]:
        objects: list[MemoryObject] = []
        for index, chunk in enumerate(conv.text.split("\n\n")):
            cleaned = chunk.strip()
            if not cleaned:
                continue
            objects.append(
                MemoryObject(
                    id=f"mem-{conv.id}-{index}",
                    mtype=MemoryType.CONCEPT,
                    definition=cleaned,
                    evidence_refs=[],
                    lineage=[conv.id],
                    version=Version("v0.1.0"),
                    continuity_thread=conv.continuity_thread,
                )
            )
        return objects
