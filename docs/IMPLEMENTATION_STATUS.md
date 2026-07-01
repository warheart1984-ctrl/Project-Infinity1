# Constitutional Implementation Status

## Purpose

This document separates implemented guarantees from external dependencies and
planned capabilities for the local Ollama architect-agent integration. A
capability is listed as implemented only when source code and an executable
test exist in this repository.

## Implemented

### Architect Runtime

Status: implemented.

`packages/architect-agent/src/architectAgent.ts` composes model proposal
generation, UCR evaluation, ALA normalization, safety evaluation, envelope
construction, replay, and receipt generation. It returns a governed proposal
result without applying filesystem changes.

Evidence:

- `packages/architect-agent/src/architectAgent.test.ts`
- accepted and rejected proposal paths
- receipt and replay assertions
- no applied-filesystem result surface

### Builder Runtime

Status: implemented for structured proposal construction.

`packages/architect-agent/src/prompt.ts` creates the bounded model instruction,
`ollamaProvider.ts` performs non-streaming generation, and `proposal.ts`
validates model output before it reaches governance.

Implemented guarantees:

- `qwen2.5-coder:3b` default
- configurable model identifier, including `qwen2.5-coder:7b`
- request timeout with abort
- bounded `num_predict`
- non-streaming JSON response
- strict schema, goal, operation, path, and content validation
- sanitized provider errors that do not include prompts or raw responses

Evidence:

- `packages/architect-agent/src/proposal.test.ts`
- `packages/architect-agent/src/ollamaProvider.test.ts`

### Integration Runtime

Status: implemented for the standalone AAES-OS TypeScript runtime.

`aaes-os/src/model/OllamaProvider.ts` preserves the AAES model-provider surface
and delegates transport and validation to `@aaes-os/architect-agent`.

Evidence:

- `aaes-os/tests/OllamaProvider.test.ts`
- `npm run test:model` from `aaes-os`

Lawful Nova provides the corresponding governed Python and Electron model
routes in the separate `agentic-coding-agent` repository.

### Safety Runtime

Status: implemented for proposal-level pre-execution checks.

`evaluateSafety` rejects empty insert/update content and paths that escape the
workspace. `evaluateUcr` separately enforces goal, operation, and authorized
file constraints. An architect result is accepted only when both decisions
pass.

Evidence:

- `packages/architect-agent/src/governance.ts`
- `packages/architect-agent/src/governance.test.ts`

### Replay

Status: implemented for governed proposal replay.

`replayEnvelope` recomputes the proposal hash, UCR decision, normalized ALA
plan, safety decision, and timestamp validity. It reports drift without
executing model inference or filesystem mutations.

Evidence:

- clean replay test
- tampered ALA plan test
- rejected-proposal replay test

### EGL-1

Status: implemented for proposal and governance-decision equivalence.

The current EGL-1 profile considers a replay equivalent when:

1. the proposal content hash matches,
2. UCR produces the same decision and reasons,
3. ALA produces the same normalized operation plan,
4. Safety produces the same decision and violations, and
5. the envelope timestamp is valid.

Filesystem-state equivalence is not claimed because the architect runtime does
not include a filesystem executor.

### Deterministic Envelopes

Status: implemented for deterministic content identity.

`hashStable` sorts object keys recursively before SHA-256 hashing. Equivalent
proposal objects therefore receive the same `proposalHash` regardless of input
key order.

The envelope also records an issuance timestamp. Complete serialized envelopes
created at different times are intentionally not byte-for-byte identical; the
deterministic guarantee applies to proposal identity and replayed decisions.

### Threat Model

Status: implemented for the local proposal boundary.

| Threat | Implemented control |
|---|---|
| Malformed model output | Strict JSON parsing and runtime schema validation |
| Partial streamed JSON | Ollama generation uses `stream: false` |
| Unbounded generation | Positive integer `maxTokens` mapped to `num_predict` |
| Hung local endpoint | AbortController timeout |
| Path traversal | Absolute paths and `..` segments rejected |
| Unauthorized mutation proposal | Goal, operation, and file contract checks |
| Empty destructive patch | Insert/update content must be non-empty |
| Prompt or response disclosure in errors | Sanitized typed error messages |
| Hidden filesystem side effects | Runtime produces proposals only |
| Replay drift | Hash and decision recomputation |

This threat model does not claim hardware isolation, key custody, process
sandboxing, or host compromise resistance.

### Conformance Tests

Status: implemented.

Current feature matrix:

- architect-agent package: 28 tests
- AAES root compatibility adapter: 1 test
- AAES standalone runtime: 27 tests
- governance-genome gate: 199 genomes valid
- formerly blocked API modules: 251 tests passed
- strict TypeScript package build
- live `qwen2.5-coder:3b` proposal generation
- whitespace validation
- credential-pattern scan

## External

### Hardware Root of Trust

No TPM, HSM, secure enclave, measured boot, or hardware attestation integration
is included.

### Key-Backed Signatures

Receipts and envelopes use deterministic hashes, not asymmetric signatures.
Private-key custody, rotation, verification, and revocation are external.

### Durable Receipt Ledger

`ArchitectAgent.run` returns a receipt with each result. It does not persist
receipts across processes. Database-backed append-only storage is external.

### Filesystem Executor

The runtime does not write, delete, rename, or execute proposed files.
Application, rollback, workspace snapshots, and filesystem authorization are
external.

### Federated Trust

Cross-node identity, quorum, remote attestation, trust exchange, and federated
receipt verification are external.

## Planned

### Persistent Evidence Corpus

Store envelopes, receipts, replay outcomes, model metadata, and conformance
evidence in an append-only durable corpus.

### Multi-Node Federation

Add governed node identity, trust negotiation, receipt exchange, and explicit
federation policy.

### Advanced Equivalence Profiles

Extend EGL-1 with filesystem snapshots, semantic code equivalence, toolchain
version binding, and configurable equivalence tolerances.

### Production Trust Infrastructure

Add key-backed signatures, secure key custody, rotation, revocation,
attestation, deployment hardening, and operational monitoring.

## Repository Baseline

The feature-specific tests pass after rebasing onto current `origin/main`.
The standalone AAES public export is restored, and all genome proof paths are
repository-relative. Strict genome validation passes for 199 genomes, and the
four previously blocked API modules pass all 251 tests.

GitHub Actions remains externally blocked by the account billing lock, and npm
publication remains blocked until the local npm client is authenticated. These
constraints are documented in
`docs/baseline-debt/local-ollama-architect-agent.md`.
