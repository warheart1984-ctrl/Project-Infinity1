"""FOS kernel tests."""

from __future__ import annotations

from src.continuity.cab import CABLedger
from src.fos.decision_ledger import DecisionLedger, FosDecision
from src.fos.kernel import FosKernel
from src.fos.memory_core import MemoryCore
from src.fos.translation import RawConversation
from src.fos.validation import ValidationLayer
from src.fos.types import MemoryObject, MemoryType


def test_ingest_conversation_creates_valid_memory():
    kernel = FosKernel(memory=MemoryCore())
    conv = RawConversation(
        id="conv-001",
        text="FOS captures founder cognition.\n\nArchitecture becomes first-class.",
        continuity_thread="thread-fos-v0.1",
    )
    ids = kernel.ingest_conversation(conv)
    assert len(ids) == 2
    for object_id in ids:
        obj = kernel.memory.get(object_id)
        assert obj is not None
        assert ValidationLayer.validate_memory(obj)


def test_compile_architecture_blueprint_emits_continuity_event():
    kernel = FosKernel(memory=MemoryCore())
    kernel.memory.upsert(
        MemoryObject(
            id="arch-001",
            mtype=MemoryType.ARCHITECTURE,
            definition="Layered runtime with governance substrate",
            lineage=["conv-001"],
            continuity_thread="thread-fos-v0.1",
        )
    )
    event = kernel.compile_architecture_blueprint("thread-fos-v0.1")
    assert event["type"] == "Blueprint"
    assert event["thread_id"] == "thread-fos-v0.1"


def test_validation_rejects_empty_definition():
    obj = MemoryObject(
        id="bad-001",
        mtype=MemoryType.CONCEPT,
        definition="   ",
        lineage=["src"],
        continuity_thread="thread-x",
    )
    assert not ValidationLayer.validate_memory(obj)


def test_fos_decision_syncs_to_cab():
    memory = MemoryCore()
    ledger = CABLedger()
    decisions = DecisionLedger(memory)
    fos_decision = FosDecision(
        id="fos.decision.test",
        rationale="Enable FOS substrate in URG",
        chosen_option="implement-v0.1",
        alternatives=[{"option_id": "defer", "label": "Defer FOS"}],
        continuity_thread="thread-fos-v0.1",
        intent_refs=["cab.intent.nova-in-urg"],
    )
    decisions.record(fos_decision)
    cab_record = decisions.sync_to_cab(fos_decision, ledger=ledger)
    assert cab_record.decision_id == "cab.decision.fos.fos.decision.test"
    assert ledger.get_latest(cab_record.decision_id) is not None
