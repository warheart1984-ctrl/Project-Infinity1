"""AAIS ReconstructionHarness — load → graph → replay → aggregate."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.aais.reconstruction.graph import build_lineage_graphs
from src.aais.reconstruction.replay import replay_thread
from src.aais.reconstruction.types import (
    ContinuityEvent,
    ContinuityProofReconstruction,
    LineageGraph,
    ThreadProof,
)
from src.aais.reconstruction.wire import load_wire

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WIRE_SCHEMA = REPO_ROOT / "schemas" / "continuity_wire.v1.json"
DEFAULT_PROOF_SCHEMA = REPO_ROOT / "schemas" / "continuity_proof.reconstruction.v1.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_wire_fingerprint(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


class ReconstructionHarness:
    """Read continuity.jsonl → reconstruct lineage → emit ContinuityProof.reconstruction."""

    def __init__(
        self,
        wire_path: str | Path,
        wire_schema_path: str | Path | None = None,
        proof_schema_path: str | Path | None = None,
    ) -> None:
        self.wire_path = Path(wire_path)
        self.wire_schema_path = Path(wire_schema_path or DEFAULT_WIRE_SCHEMA)
        self.proof_schema_path = Path(proof_schema_path or DEFAULT_PROOF_SCHEMA)
        self._invalid_wire_findings: list[dict[str, Any]] = []
        self._thread_parents: dict[str, str | None] = {}

    def load_wire(self) -> list[ContinuityEvent]:
        events, threads, invalid = load_wire(self.wire_path, schema_path=self.wire_schema_path)
        self._invalid_wire_findings = invalid
        self._thread_parents = {
            str(record["thread_id"]): (
                str(record["parent_thread_id"]) if record.get("parent_thread_id") else None
            )
            for record in threads
        }
        for event in events:
            self._thread_parents.setdefault(event.thread_id, None)
        return events

    def build_lineage_graphs(self, events: list[ContinuityEvent]) -> dict[str, LineageGraph]:
        return build_lineage_graphs(events, thread_parents=self._thread_parents)

    def replay_thread(
        self,
        graph: LineageGraph,
        *,
        all_events: dict[str, ContinuityEvent] | None = None,
    ) -> ThreadProof:
        return replay_thread(graph, all_events=all_events)

    def aggregate(self, proofs: list[ThreadProof]) -> dict[str, Any]:
        global_orphans = all(proof.invariants["no_orphaned_events"] for proof in proofs) if proofs else True
        global_broken = all(proof.invariants["no_broken_lineage"] for proof in proofs) if proofs else True
        source = str(self.wire_path)
        if self.wire_path.exists():
            source = f"{source}#{source_wire_fingerprint(self.wire_path)}"

        reconstruction = ContinuityProofReconstruction(
            version="v1",
            generated_at=_now_iso(),
            source_wire=source,
            threads=proofs,
            global_={
                "threads_analyzed": len(proofs),
                "invariants": {
                    "no_orphaned_events": global_orphans,
                    "no_broken_lineage": global_broken,
                },
            },
        )
        return reconstruction.to_dict()

    def run(self, *, output_path: Path | None = None) -> dict[str, Any]:
        events = self.load_wire()
        all_events = {event.event_id: event for event in events}
        graphs = self.build_lineage_graphs(events)
        proofs = [self.replay_thread(graph, all_events=all_events) for graph in graphs.values()]
        if self._invalid_wire_findings and proofs:
            proofs[0].findings.extend(self._invalid_wire_findings)
        payload = self.aggregate(proofs)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return payload
