# AAIS — Adaptive Assistant Intelligence System
 
> Behavior enforced, not implied.
 
[![Tests](https://img.shields.io/badge/tests-pytest-blue)](tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
 
---
 
## What Is This?
 
AAIS is a local-first assistant runtime where behavior is governed by explicit law, not left to inference.
 
Every request passes through a bridge-enforced ingress layer. Every decision leaves a trace. When the system reroutes, pauses, or blocks — you see why.
 
It ships with:
 
- **Bridge-enforced ingress** — fail-closed by default, no silent pass-through
- **Signed, time-bound attestation** — nonce-backed, replay and tamper rejection built in
- **Governed memory and workflow paths** — bounded authority per layer, no cross-layer drift
- **Visible operator traces** — why something passed, was blocked, or was downgraded
This is not "trust me." It is "test it."
 
---
 
## Why Is This Different?
 
Most assistant projects optimize for output first. AAIS optimizes for behavior first.
 
That means:
 
- One clear operating contract per turn
- Normal work and risky or experimental work stay separated
- The system shows when it reroutes, pauses, or blocks — it does not hide decisions
- Operator control is preserved, not abstracted away
The core doctrine is [Stabilize and Free](docs/spine/STABILIZE_AND_FREE.md): stability before freedom. The system earns more responsibility by staying inside clear rules, explaining its behavior, and failing in a controlled way. If it cannot do that, it slows down, asks for confirmation, or stops.
 
---
 
## Quick Start
 
```bash
pip install -e .
python -m aais start --data-dir ./.runtime/aais-data
```
 
Then open:
 
| Surface | URL |
|---|---|
| App | http://127.0.0.1:8000/app |
| Jarvis Console | http://127.0.0.1:8000/app/jarvis |
| Health | http://127.0.0.1:8000/health |
 
**Before launching** (optional preflight):
 
```bash
python -m aais prepare --force-build --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data
```
 
**Frontend dev server** (if not using the packaged shell):
 
```bash
# From /frontend
npm install && npm run dev
```
 
Surfaces at `localhost:3000/jarvis`, `localhost:3000/workbench`, `localhost:3000/memory`.
 
---
 
## Requirements
 
Use `requirements.txt` for standard local setup. The other requirements files cover specific environments:
 
| File | Use |
|---|---|
| `requirements.txt` | Standard local |
| `requirements-local.txt` | Local with dev extras |
| `requirements-laptop.txt` | Constrained/laptop env |
| `requirements-advanced.txt` | Full feature set |
| `requirements-training.txt` | Training pipeline only |
 
---
 
## Optional: Claude Provider
 
Claude support ships with the standard Python requirements.
 
```env
ANTHROPIC_API_KEY=your_key_here
AAIS_CLAUDE_MODEL=claude-sonnet-4-20250514       # optional override
AAIS_ENABLE_CLAUDE_AUTO_ROUTING=true              # routes eligible turns automatically
```
 
To pin Claude instead of auto-routing, start a session with `provider_mode=claude_first` or select it in the Jarvis Console provider controls.
 
---
 
## Repository Structure
 
```
aais/                  Core runtime
api/                   API surface
app/                   Packaged shell and workflow infrastructure
src/                   jarvis_operator.py, api.py — main entry points
docs/
  spine/               Canonical project explanation
  runtime/             Runtime and system references
  contracts/           Laws and contracts
  subsystems/          Subsystem-specific packs
  audit/               Status and audit material
  _archive/            Lineage and reference — not active authority
  _future/             Planned — not live
engine/                Internal foundation layer
forge/                 Bounded contractor lane
evolve_engine/         Outcome-based adaptation layer
evals/                 Evaluation harness
tests/                 Test suite
```
 
Only `docs/` (excluding `_archive/` and `_future/`) is authoritative for runtime understanding.
 
---
 
## Key Internal Layers
 
| Layer | Role |
|---|---|
| **Jarvis** | Main authority lane — operator-facing ingress and runtime control |
| **Forge** | Bounded contractor lane — isolated code execution |
| **OTEM** | Bounded task and memory support |
| **Workflow shell** | Packaged app route layer |
| **Evolve engine** | Learns from outcomes — does not alter role definitions |
 ## Core Cognitive Architecture

**[Cognitive Architecture Signature: Unified Architectural Hyper-Systemizer][(ZENODO_LINK_HERE)](https://zenodo.org/records/20067067)**  
Formal specification of the cognitive engine behind Project Infinity (May 5, 2026).
---
 
## What to Read Next
 
1. [AAIS Human Guide](docs/spine/AAIS_HUMAN_GUIDE.md)
2. [AAIS AI Operating Contract](docs/spine/AAIS_AI_OPERATING_CONTRACT.md)
3. [AAIS Master Spec](docs/spine/AAIS_MASTER_SPEC.md)
4. [AAIS Runtime Guide](docs/runtime/AAIS_RUNTIME_GUIDE.md)
5. [AAIS Documentation Map](docs/README.md)
---
 
## Project Laws
 
| Document | What It Governs |
|---|---|
| [README Law v1](docs/contracts/README_LAW_V1.md) | How documentation is written and maintained |
| [External Suggestion Admission Rule](docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md) | How external input enters the system |
| [ARIS Runtime Contract](docs/contracts/ARIS_RUNTIME_CONTRACT.md) | Embedded repo-intelligence law |
| [AAIS Cognitive Bridge Runtime Law](docs/contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md) | Bridge ingress and attestation rules |
 
The full repo operating law is in [REPO_LAWBOOK.md](REPO_LAWBOOK.md).
 
---
 
## Security
 
See [SECURITY.md](SECURITY.md) for the disclosure policy.
 
---
 
## License
 
[Apache 2.0](LICENSE)
---

---

## Points of Interest (for the curious)

This repository contains more than the visible surface suggests.  
Most of the system is layered, and some components only reveal themselves when explored in depth.

A few optional areas to investigate:

### Internal Architecture Layers
Several subsystems are structured in nested layers.  
Some folders contain lineage documents, early doctrine, or internal evolution notes that show how the system’s behavior and philosophy developed over time.

### Foundation Artifacts
The `engine/` directory includes a foundational layer that holds structural invariants and internal markers.  
These are not required for normal operation, but they provide insight into the system’s design principles and long-term stability model.

### Historical & Lineage Documents
The `docs/_archive/` tree contains older specifications, prototypes, and conceptual drafts.  
These documents are not authoritative, but they reveal the system’s evolution and the reasoning behind certain design choices.

### Compiler Behavior
Certain internal components maintain their own metadata or narrative traces as new subsystems are added.  
This is intentional and part of the system’s introspective design.

These points are optional and not required for running the demo.  
They exist for those who enjoy exploring deeper layers of a system’s architecture.

---

### A Note for Deep Explorers
Some structures in this repository serve both functional and protective roles.  
Most users will never encounter them, but those who explore the deeper layers  
may notice patterns of separation, guardianship, and intentional design.

This is expected.
