# AAIS Reconstruction Harness

Status: executable spec v1

## Purpose

Read `continuity.jsonl` (universal language), reconstruct AAIS-relevant lineage, replay
events, and emit **`ContinuityProof.reconstruction`** for one or more threads.

Given only the wire, AAIS can:

- rebuild what happened
- check continuity invariants
- surface where continuity holds or breaks

## Contracts

| Role | Path |
|------|------|
| Input wire | [`../../schemas/continuity_wire.v1.json`](../../schemas/continuity_wire.v1.json) |
| Output proof | [`../../schemas/continuity_proof.reconstruction.v1.json`](../../schemas/continuity_proof.reconstruction.v1.json) |

Wire records (`record_type: event`) normalize internally to:

```json
{
  "thread_id": "string",
  "event_id": "string",
  "parent_event_id": "string|null",
  "timestamp": "ISO8601",
  "kind": "Evidence|Decision|Error|Correction|Override|Meta|...",
  "lineage": { "causal": ["..."], "thread": "thread_id" },
  "payload": {}
}
```

## Module layout

```
src/aais/reconstruction/
  __init__.py
  types.py      # ContinuityEvent, LineageGraph, ThreadProof
  wire.py       # strict load + validate
  graph.py      # lineage graphs (roots, orphans, cycles)
  replay.py     # ReplayState + invariants
  harness.py    # ReconstructionHarness.run()
```

## Harness interface

```python
harness = ReconstructionHarness(
    wire_path="continuity.jsonl",
    wire_schema_path="schemas/continuity_wire.v1.json",
    proof_schema_path="schemas/continuity_proof.reconstruction.v1.json",
)
proof = harness.run(output_path=Path("continuity_proof.reconstruction.json"))
```

## Invariants (baked into proof schema)

**Per thread:** `no_orphaned_events`, `no_broken_lineage`, `no_unbacked_decisions`

**Global:** AND of per-thread `no_orphaned_events` and `no_broken_lineage`

## Stack fit

```text
DAR-Z  → writes Evidence + Decision
FOS    → reads + reconstructs
AAIS   → reads + proves
```

One universal language. Three projections. Zero FFI.

## Verification

```powershell
pytest tests/test_aais_reconstruction_harness.py tests/test_darz_reconstruction_harness.py -q
make aais-reconstruction-gate
```

Fixture: [`../../fixtures/fos/aais_lineage_reconstruction.v1.json`](../../fixtures/fos/aais_lineage_reconstruction.v1.json)

DAR-Z integration fixture: [`../../fixtures/fos/darz_lineage_reconstruction.v1.json`](../../fixtures/fos/darz_lineage_reconstruction.v1.json)

FOS cross-thread fixture: [`../../fixtures/fos/fos_cross_thread_reconstruction.v1.json`](../../fixtures/fos/fos_cross_thread_reconstruction.v1.json) (merges AAIS + DAR-Z + FOS on one wire)

NexusOS civilization fixture: [`../../fixtures/fos/nexusos_lineage_reconstruction.v1.json`](../../fixtures/fos/nexusos_lineage_reconstruction.v1.json) (full four-thread civilization wire)
