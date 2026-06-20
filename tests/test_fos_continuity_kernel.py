"""FOS minimal kernel tests — three primitives + projections."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.fos.continuity import ContinuityEngine
from src.fos.kernel import FosKernel
from src.fos.primitives import EventType
from src.fos.projections import ContinuityThreadExplorer, FounderMemoryVault, LineageGraph
from src.fos.reconstruction import ReconstructionEngine


@pytest.fixture
def isolated_engine(tmp_path: Path) -> ContinuityEngine:
    return ContinuityEngine(store_path=tmp_path / "continuity.jsonl")


def test_kernel_create_thread_append_event_query_lineage(isolated_engine: ContinuityEngine):
    engine = isolated_engine
    engine.create_thread("thread-root")
    concept = engine.append_event(
        "thread-root",
        EventType.CONCEPT.value,
        {"definition": "FOS is continuity substrate"},
        lineage=[],
    )
    decision = engine.append_event(
        "thread-root",
        EventType.DECISION.value,
        {
            "rationale": "Adopt minimal kernel",
            "chosen_option": "three-primitives",
            "alternatives": [{"option_id": "monolith", "label": "Keep monolithic modules"}],
        },
        lineage=[concept.event_id],
    )
    thread_events = engine.query_thread("thread-root")
    assert len(thread_events) == 2
    lineage = engine.query_lineage(decision.event_id)
    assert lineage[0].event_id == decision.event_id
    assert any(item.event_id == concept.event_id for item in lineage)
    pointers = engine.lineage_pointers(decision.event_id)
    assert pointers[0].to_event_id == concept.event_id


def test_reconstruction_engine_follows_lineage_backward(isolated_engine: ContinuityEngine):
    engine = isolated_engine
    engine.create_thread("thread-decision")
    concept = engine.append_event(
        "thread-decision",
        EventType.CONCEPT.value,
        {"definition": "We need reconstructability"},
    )
    evidence = engine.append_event(
        "thread-decision",
        EventType.EVIDENCE.value,
        {"definition": "pytest pass", "evidence_refs": ["ev:test:001"]},
        lineage=[concept.event_id],
    )
    decision = engine.append_event(
        "thread-decision",
        EventType.DECISION.value,
        {
            "rationale": "Ship continuity kernel first",
            "chosen_option": "kernel-first",
            "alternatives": [{"option_id": "ui-first", "label": "Build UI first"}],
            "evidence_refs": ["ev:test:001"],
        },
        lineage=[evidence.event_id, concept.event_id],
    )
    report = ReconstructionEngine(engine).reconstruct(decision.event_id)
    assert report["chosen_option"] == "kernel-first"
    assert report["alternatives"]
    assert report["evidence_refs"] == ["ev:test:001"]
    assert concept.event_id in report["lineage"]


def test_projections_vault_graph_explorer(tmp_path: Path):
    kernel = FosKernel(continuity=ContinuityEngine(store_path=tmp_path / "continuity.jsonl"))
    kernel.continuity.create_thread("thread-proj")
    kernel.continuity.append_event(
        "thread-proj",
        EventType.ARCHITECTURE.value,
        {"definition": "DAR-Z consumes FOS memory"},
    )
    kernel.continuity.append_event(
        "thread-proj",
        EventType.DECISION.value,
        {"rationale": "Bundle Nova in URG", "chosen_option": "bundle-in-urg"},
    )
    vault = FounderMemoryVault(kernel.continuity)
    assert len(vault.list_events(thread_id="thread-proj")) >= 2
    graph = LineageGraph(kernel.continuity).build()
    assert len(graph["nodes"]) >= 2
    explored = ContinuityThreadExplorer(kernel.continuity).explore("thread-proj")
    assert explored["event_count"] >= 2
    assert explored["chain"]


def test_fos_kernel_reconstruct_decision_integration(tmp_path: Path):
    kernel = FosKernel(continuity=ContinuityEngine(store_path=tmp_path / "continuity.jsonl"))
    kernel.create_thread("thread-integration")
    concept_id = kernel.continuity.append_event(
        "thread-integration",
        EventType.CONCEPT.value,
        {"definition": "Continuity is the substrate"},
    ).event_id
    decision_id = kernel.continuity.append_event(
        "thread-integration",
        EventType.DECISION.value,
        {
            "rationale": "Everything else is a projection",
            "chosen_option": "minimal-kernel",
            "alternatives": [],
        },
        lineage=[concept_id],
    ).event_id
    report = kernel.reconstruct_decision(decision_id)
    assert report["rationale"] == "Everything else is a projection"
    graph = kernel.build_lineage_graph()
    assert any(edge.get("from_event_id") == decision_id for edge in graph["edges"])
