# FOS v0.1 Architecture (Founder Operating System)

Status: executable substrate in URG-Cloud-Platform

FOS is a persistent, governed institutional memory substrate. It is not an agent,
decision-maker, or execution system. It structures founder cognition into reusable
architecture, governance, and evidence artifacts that other systems consume.

## Purpose

FOS exists to:

1. Capture founder cognition
2. Structure it into institutional memory
3. Compile it into architecture
4. Bind it to governance
5. Validate it with evidence
6. Preserve long-term continuity

## Causal pipeline

```text
Conversation → Structured Memory → Architecture → Governance → Evidence → Institutional Knowledge
```

Implementation path in URG:

```text
RawConversation
  → TranslationEngine
  → MemoryCore
  → BlueprintCompiler / Registries
  → CAB bridge (IntentRecord, DecisionRecord, ContinuityReceipt)
  → ControlTower console (readout)
```

## Minimal kernel (bedrock)

The irreducible FOS kernel is **three primitives**. Everything else is a projection.

| Primitive | Module | Fields |
|-----------|--------|--------|
| ContinuityThread | `src/fos/primitives.py` | `thread_id`, `parent_thread_id?`, `event_ids[]` |
| ContinuityEvent | `src/fos/primitives.py` | `event_id`, `thread_id`, `type`, `payload`, `timestamp`, `lineage[]` |
| LineagePointer | `src/fos/primitives.py` | `from_event_id` → `to_event_id` |

**ContinuityEngine** (`src/fos/continuity.py`) implements Step 1:

- `create_thread`
- `append_event`
- `query_thread`
- `query_lineage`

**Event types** (Step 2): Concept, Architecture, Governance, Decision, Evidence.

**Projections** (Steps 3–5, above the kernel):

| Projection | Module | Role |
|------------|--------|------|
| Decision Reconstruction Engine | `src/fos/reconstruction.py` | Given event ID → lineage, rationale, evidence, alternatives |
| Lineage Graph | `src/fos/projections.py` | Event graph from lineage pointers |
| Founder Memory Vault | `src/fos/projections.py` | Filtered continuity events |
| Continuity Thread Explorer | `src/fos/projections.py` | Decision → Architecture → Governance → Evidence chain |

Legacy modules (MemoryCore, registries, blueprint compiler) remain as **compatibility projections**
that write through `ContinuityEngine`.

## Core components (projections + compatibility)

| Component | Module | Role |
|-----------|--------|------|
| Founder Memory Core | `src/fos/memory_core.py` | Persistent memory objects |
| Architecture Registry | `src/fos/architecture_registry.py` | System models and blueprints |
| Governance Registry | `src/fos/governance_registry.py` | Invariants and governance contracts |
| Decision Ledger | `src/fos/decision_ledger.py` | FOS decisions with CAB sync |
| Translation Engine | `src/fos/translation.py` | Conversation → memory (v0.1 paragraph split) |
| Blueprint Compiler | `src/fos/blueprint.py` | Memory → architecture/governance blueprints |
| Validation Layer | `src/fos/validation.py` | Memory integrity rules |
| Continuity Engine | `src/fos/continuity.py` | Continuity events on transforms |
| CAB bridge | `src/fos/cab_bridge.py` | FOS ↔ CAB type mapping |
| Symbolic bridge | `src/fos/symbolic_bridge.py` | Symbolic organism coherence → CAB/FOS |
| Kernel | `src/fos/kernel.py` | Orchestrator API |

Parallel Rust kernels:

- **`civilization-stack/`** — canonical FOS continuity substrate (threads, events, lineage, reconstruction). Gate: `make civilization-stack-gate`.
- **`darz-kernel/`** — DAR-Z validator + FOS wire coupling. Gate: `make darz-kernel-gate`.

AAIS reconstruction harness (Python):

- **`src/aais/reconstruction/`** — reads `continuity.jsonl`, emits `ContinuityProof.reconstruction`. Gate: `make aais-reconstruction-gate`.
- Contract: [`docs/contracts/AAIS_RECONSTRUCTION_HARNESS.md`](AAIS_RECONSTRUCTION_HARNESS.md)

## Constitutional charter (summary)

**Article I — Identity:** FOS is memory + compilation + continuity substrate.

**Article II — Authority:** FOS has no execution authority. It may structure, compile,
bind, validate, and emit continuity. It may not execute actions, allocate resources,
override governance, or produce binding decisions.

**Article III — Obligations:** Preserve continuity, bind evidence, enforce invariants,
maintain coherence, version all memory, record lineage, expose interfaces, remain
substrate-neutral.

**Article IV — Rights:** Request missing context/evidence; refuse compilation on invariant failure.

**Article V — Amendments:** No amendment may grant FOS execution authority.

## Ontology v1.0

Memory object types: Concept, Pattern, Invariant, Architecture, GovernanceContract,
Decision, Evidence, ContinuityThread, SystemModel, Blueprint, FieldDefinition.

Required fields: `id`, `mtype`, `definition`, `evidence_refs`, `lineage`, `version`,
`continuity_thread`.

Integrity rules (v0.1 baseline):

- No object without definition, version, type, continuity thread
- Strict mode also requires lineage (see `ValidationLayer.validate_memory_strict`)

## Integration layers

### DAR-Z

- Consumer: concepts, invariants, architectures from FOS (`src/fos/integrations/darz.py`)
- Producer: reasoning traces → FOS evidence memory

### GSCE

- GSCE defines validation rules; FOS validation layer enforces (`src/fos/integrations/gsce.py`)

### Nova / AAIS / AAES

- Nova continuity receipts ingested into CAB (`ingest_nova_continuity_governance`)
- Optional FOS evidence sync when `FOS_NOVA_SYNC=1`

### ControlTower

- Operator console exposes CAB lineage section (`src/continuity/cab_console.py`)
- Console version `1.4` includes `cab` snapshot block

### NeoMundi

- Measurements ingested to CAB EvidenceChain (`src/neomundi/`)

### CIEMS (Mutation Engine)

- Successful mutations linked to CAB DecisionRecord when `CAB_CIEMS_AUTO_LINK=1`
- Bridge: `src/continuity/cab_ciems_bridge.py`

### Symbolic organism

- Governed VM with continuity lineage and coherence receipts (`src/symbolic_organism/`)
- Coherent promotion ingested via `src/fos/symbolic_bridge.py`

## Environment variables

| Variable | Purpose |
|----------|---------|
| `FOS_STORE` | FOS JSONL memory store (default `.runtime/fos/memory.jsonl` or `~/.fos/memory.jsonl`) |
| `CAB_STORE` | CAB ledger path |
| `CAB_CIEMS_AUTO_LINK` | Mutation apply → CAB DecisionRecord |
| `CAB_CIEMS_INTENT_ID` | Optional intent back-link for CIEMS decisions |
| `CAB_AUTO_INGEST` | Nova turn → CAB ContinuityReceipt |
| `FOS_NOVA_SYNC` | Nova receipt → FOS evidence memory |
| `NEOMUNDI_MEASUREMENT_DIR` | Local NeoMundi measurement ingest directory |

## Schema

- FOS: `schemas/fos.v1.json`
- CAB: `schemas/cab.v1.json`

## Verification

```powershell
$env:LAWFUL_NOVA_REPO_ROOT = "e:\urg-wt"
$env:PYTHONPATH = "e:\urg-wt"
e:\urg-wt\tools\bin\python3.cmd -m pytest tests/test_fos_kernel.py tests/test_cab_blueprint.py tests/test_neomundi_cab_ingest.py tests/test_cab_console.py tests/test_symbolic_organism_vm.py tests/test_symbolic_bridge.py -q
```

Rust kernels:

```powershell
cd civilization-stack
cargo test

cd fos-kernel
cargo test
```

## Scope boundaries (v0.1)

Not included: full research knowledge graph DB, multi-author RBAC, LLM translation,
live NeoMundi telemetry pipeline, GSCE as executable runtime.
