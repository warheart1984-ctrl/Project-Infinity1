# Local Ollama Architect Agent Design

## Objective

Add a production-quality local coding-model path to Project Infinity and Lawful
Nova using the Ollama models already installed on the workstation:

- `qwen2.5-coder:3b` as the default
- `qwen2.5-coder:7b` as an explicit configuration option

The work is delivered in three sequential stages:

1. Create the `@aaes-os/architect-agent` workspace package.
2. Replace the root `src/model/OllamaProvider.ts` stub with a compatibility
   adapter.
3. Restore and update the `lawful-nova-shell` source checkout.

## Architecture

### Workspace Package

`packages/architect-agent` owns the TypeScript model-provider contract,
proposal schema, Ollama HTTP client, and governed architect-agent pipeline.
The package uses the workspace's existing Node.js 20, TypeScript, and Vitest
toolchain and adds no runtime dependency for HTTP or UUID generation.

The Ollama client calls `/api/generate` with streaming disabled. It sends
deterministic generation options, including temperature and output-token
limits, and requests JSON output. The response is parsed and validated before
it enters the governance pipeline.

### Root Compatibility Adapter

The root `src/model/OllamaProvider.ts` preserves the existing
`ModelProvider.generate(prompt)` contract. It delegates generation to the
workspace package and returns the validated proposal shape expected by current
root consumers.

The root adapter contains no hard-coded proposal and no independent HTTP
implementation.

### Lawful Nova

The current `E:\project-infi\lawful-nova-shell` directory contains generated
runtime artifacts and Python bytecode but not editable source. Its contents
will be preserved in a sibling backup directory. The editable source will be
restored from the dedicated `warheart1984-ctrl/agentic-coding-agent`
repository, using the latest branch that contains the desktop Node and local
model surfaces.

The restored Python and Electron implementations remain native to their
language. They use the same observable configuration contract as the
TypeScript package:

- Ollama base URL
- model name
- timeout
- temperature
- maximum output tokens

The default becomes `qwen2.5-coder:3b`; `qwen2.5-coder:7b` remains selectable
through environment/configuration and the desktop model selector.

## Public Contracts

### Architect Agent Options

The package accepts:

- `baseUrl`: defaults to `http://127.0.0.1:11434`
- `model`: defaults to `qwen2.5-coder:3b`
- `timeoutMs`: finite positive integer
- `temperature`: finite number from 0 through 2
- `maxTokens`: positive integer
- injectable `fetch` implementation for deterministic tests

### Model Proposal

A valid proposal contains:

- `schemaVersion` equal to `"1"`
- a supported goal
- an operations array
- each operation has a non-empty relative file path
- operation type is `insert`, `update`, or `delete`
- insert/update content is non-empty
- delete content is absent or null

Unknown fields are ignored only when they do not weaken these invariants.
Malformed or unsupported output is rejected before governance evaluation.

### Error Contract

The provider emits typed errors for:

- invalid configuration
- request timeout
- network or HTTP failure
- empty model response
- malformed JSON
- proposal-schema violation

Error messages may contain endpoint and status information but must not expose
environment variables, prompt contents, credentials, or complete provider
responses.

## Data Flow

1. A caller submits a coding prompt.
2. The provider builds the structured JSON prompt.
3. Ollama returns one non-streaming response.
4. The package extracts and validates the proposal.
5. The architect agent evaluates UCR constraints.
6. ALA normalizes the allowed operations.
7. Safety evaluates the normalized plan with the proposal and contract.
8. The envelope builder creates a deterministic proposal hash and audit
   timestamp.
9. Replay re-evaluates the same governed decisions and reports drift.
10. The caller receives the proposal, envelope, replay result, and receipt.

Model generation proposes changes only. It does not write files or execute
commands.

## Testing

The TypeScript package uses mocked HTTP for:

- valid 3B response
- explicit 7B selection
- malformed JSON
- invalid proposal shape
- empty response
- non-success HTTP status
- network failure
- request timeout
- invalid provider options
- valid and rejected governed pipelines
- replay drift

The root adapter receives a focused compatibility test.

Lawful Nova verification includes:

- Python provider and tool tests
- desktop Node tests
- configuration/default-model tests
- one opt-in live Ollama generation with `qwen2.5-coder:3b`

The final readiness pass runs the complete available build and test commands,
checks CI syntax and package-lock consistency, scans changed files for secrets,
and reports both repository Git states separately.

## Git Boundaries

Project Infinity and `agentic-coding-agent` are separate publication targets.
Changes are committed only within their owning repository. Existing unrelated
changes are preserved and excluded from scoped commits.

No branch is pushed directly to `main`. Push readiness requires:

- successful build and tests
- no unintended staged files
- no generated binaries or model blobs in the patch
- confirmed remote and branch
- no hard-coded secrets
