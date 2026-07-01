# Local Ollama Architect Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested `@aaes-os/architect-agent` package, replace the root Ollama stub with a package adapter, and restore and configure Lawful Nova for the installed Qwen coding models.

**Architecture:** The TypeScript workspace package owns proposal parsing, Ollama transport, governance evaluation, deterministic envelope construction, and replay. The root provider delegates to that package. Lawful Nova keeps its Python and Electron adapters but follows the same default-model and generation-option contract.

**Tech Stack:** Node.js 20, TypeScript 5, native `fetch`, Vitest, Python 3.12, pytest, Electron, Ollama

---

## File Map

### Project Infinity

- Create `packages/architect-agent/package.json`: workspace package metadata and scripts.
- Create `packages/architect-agent/tsconfig.json`: composite TypeScript package build.
- Create `packages/architect-agent/vitest.config.ts`: package-local test discovery.
- Create `packages/architect-agent/src/types.ts`: proposal, contract, decision, envelope, and provider types.
- Create `packages/architect-agent/src/errors.ts`: typed provider error codes.
- Create `packages/architect-agent/src/proposal.ts`: strict runtime proposal validation.
- Create `packages/architect-agent/src/prompt.ts`: structured JSON generation prompt.
- Create `packages/architect-agent/src/ollamaProvider.ts`: native Ollama HTTP transport.
- Create `packages/architect-agent/src/governance.ts`: UCR, ALA, safety, envelope, and replay components.
- Create `packages/architect-agent/src/architectAgent.ts`: package orchestration entry point.
- Create `packages/architect-agent/src/index.ts`: public exports.
- Create `packages/architect-agent/src/*.test.ts`: deterministic unit and integration tests.
- Modify `tsconfig.base.json`: register the package workspace alias.
- Modify `vitest.config.ts`: register the package test alias.
- Modify `package.json`: add the package as the root compatibility dependency.
- Modify `src/model/ModelProvider.types.ts`: use a strict operation type.
- Modify `src/model/OllamaProvider.ts`: delegate to the workspace provider.
- Create `tests/model/OllamaProvider.test.ts`: verify root compatibility.

### Lawful Nova

- Preserve `E:\project-infi\lawful-nova-shell` as an artifact backup.
- Restore `warheart1984-ctrl/agentic-coding-agent` into `E:\project-infi\lawful-nova-shell`.
- Modify `nova/node/tools/local_model.py`: non-streaming Ollama generation, deterministic options, 3B default, and bounded output.
- Modify `nova/providers/provider_ollama.py`: 3B default with 7B configuration support.
- Modify `nova/config.py`: consistent 3B default.
- Modify desktop model-selection/configuration files: expose both installed Qwen models.
- Modify configuration and startup scripts: consistent model defaults.
- Modify Python and desktop tests: verify defaults, selection, payload shape, and parsing.

### Readiness

- Modify `.github/workflows/ci.yml` only if fresh verification proves the current workflow cannot install and run the workspace.
- Create no model files, generated binaries, credentials, or runtime caches.

## Task 1: Package Contract and Proposal Validation

**Files:**
- Create: `packages/architect-agent/package.json`
- Create: `packages/architect-agent/tsconfig.json`
- Create: `packages/architect-agent/vitest.config.ts`
- Create: `packages/architect-agent/src/types.ts`
- Create: `packages/architect-agent/src/errors.ts`
- Create: `packages/architect-agent/src/proposal.ts`
- Test: `packages/architect-agent/src/proposal.test.ts`

- [ ] **Step 1: Write failing proposal-validation tests**

Test valid insert/update/delete operations and reject unknown schema versions,
absolute paths, parent traversal, unsupported operation types, empty
insert/update content, and non-object model output.

```ts
expect(parseModelProposal({
  schemaVersion: '1',
  goal: 'refactor',
  operations: [{ file: 'src/index.ts', type: 'update', content: 'export {};' }],
})).toEqual({
  schemaVersion: '1',
  goal: 'refactor',
  operations: [{ file: 'src/index.ts', type: 'update', content: 'export {};' }],
});
expect(() => parseModelProposal({
  schemaVersion: '1',
  goal: 'fix',
  operations: [{ file: '../secret', type: 'update', content: 'x' }],
})).toThrowError(ArchitectAgentError);
```

- [ ] **Step 2: Run the test and verify red**

Run:
`corepack pnpm exec vitest run packages/architect-agent/src/proposal.test.ts`

Expected: FAIL because the package modules do not exist.

- [ ] **Step 3: Implement strict package types and validator**

Define:

```ts
export type OperationType = 'insert' | 'update' | 'delete';
export type ProposalGoal = 'refactor' | 'rewrite' | 'fix' | 'mutation';
export interface ModelOperation {
  file: string;
  type: OperationType;
  content?: string | null;
}
export interface ModelProposal {
  schemaVersion: '1';
  goal: ProposalGoal;
  operations: ModelOperation[];
}
```

Use explicit type guards. Normalize path separators to `/`, reject absolute
paths and `..` segments, require non-empty content for insert/update, and
normalize delete content to `null`.

- [ ] **Step 4: Run validator tests and package build**

Run:
`corepack pnpm exec vitest run packages/architect-agent/src/proposal.test.ts`

Run:
`corepack pnpm --filter @aaes-os/architect-agent build`

Expected: both commands exit 0.

## Task 2: Ollama Provider

**Files:**
- Create: `packages/architect-agent/src/prompt.ts`
- Create: `packages/architect-agent/src/ollamaProvider.ts`
- Test: `packages/architect-agent/src/ollamaProvider.test.ts`

- [ ] **Step 1: Write failing provider tests**

Inject a mocked `fetch` and assert:

```ts
expect(JSON.parse(String(init.body))).toMatchObject({
  model: 'qwen2.5-coder:3b',
  stream: false,
  format: 'json',
  options: { temperature: 0, num_predict: 2048 },
});
```

Cover explicit `qwen2.5-coder:7b`, timeout, network failure, HTTP failure,
empty response, malformed JSON, and invalid proposal output.

- [ ] **Step 2: Run the provider test and verify red**

Run:
`corepack pnpm exec vitest run packages/architect-agent/src/ollamaProvider.test.ts`

Expected: FAIL because `OllamaProvider` does not exist.

- [ ] **Step 3: Implement native-fetch transport**

Implement:

```ts
export interface OllamaProviderOptions {
  baseUrl?: string;
  model?: string;
  timeoutMs?: number;
  temperature?: number;
  maxTokens?: number;
  fetch?: typeof globalThis.fetch;
}

export class OllamaProvider {
  async generate(prompt: string): Promise<ModelProposal>;
}
```

Use `AbortController`, `/api/generate`, `stream: false`, `format: 'json'`,
typed errors, and `parseModelProposal`. Do not include prompt or raw model
output in thrown error messages.

- [ ] **Step 4: Run provider tests**

Run:
`corepack pnpm exec vitest run packages/architect-agent/src/ollamaProvider.test.ts`

Expected: all provider tests pass.

## Task 3: Governed Architect Agent

**Files:**
- Create: `packages/architect-agent/src/governance.ts`
- Create: `packages/architect-agent/src/architectAgent.ts`
- Create: `packages/architect-agent/src/index.ts`
- Test: `packages/architect-agent/src/governance.test.ts`
- Test: `packages/architect-agent/src/architectAgent.test.ts`

- [ ] **Step 1: Write failing governance and orchestration tests**

Verify allowed proposals pass, goal/file/operation violations fail closed,
operations normalize deterministically, safety rejects empty updates, proposal
hashes are stable for equivalent objects, and replay detects tampering.

```ts
const result = await agent.run('Refactor src/index.ts', contract);
expect(result.envelope.ucrDecision.ok).toBe(true);
expect(result.envelope.safetyDecision.ok).toBe(true);
expect(result.replay.ok).toBe(true);
```

- [ ] **Step 2: Run the tests and verify red**

Run:
`corepack pnpm exec vitest run packages/architect-agent/src/governance.test.ts packages/architect-agent/src/architectAgent.test.ts`

Expected: FAIL because governance modules do not exist.

- [ ] **Step 3: Implement the minimal governed pipeline**

Implement pure `evaluateUcr`, `normalizeOperations`, `evaluateSafety`,
`buildEnvelope`, and `replayEnvelope` functions. Use a stable key-sorted JSON
serializer for the SHA-256 proposal hash. `ArchitectAgent.run` generates,
evaluates, and returns data without applying filesystem mutations.

- [ ] **Step 4: Run package tests and build**

Run:
`corepack pnpm --filter @aaes-os/architect-agent test`

Run:
`corepack pnpm --filter @aaes-os/architect-agent build`

Expected: all tests and compilation pass.

- [ ] **Step 5: Commit the package**

Stage only `packages/architect-agent`, `tsconfig.base.json`,
`vitest.config.ts`, and lockfile changes. Commit:

`feat(architect-agent): add governed ollama provider`

## Task 4: Root Provider Compatibility

**Files:**
- Modify: `package.json`
- Modify: `tsconfig.base.json`
- Modify: `vitest.config.ts`
- Modify: `src/model/ModelProvider.types.ts`
- Modify: `src/model/OllamaProvider.ts`
- Create: `tests/model/OllamaProvider.test.ts`

- [ ] **Step 1: Write a failing compatibility test**

Mock injected fetch and assert the root provider returns a validated
`ModelProposal` rather than `{ raw: string }`.

```ts
const proposal = await provider.generate('Fix src/index.ts');
expect(proposal.goal).toBe('fix');
expect(proposal.operations[0]?.file).toBe('src/index.ts');
```

- [ ] **Step 2: Run the compatibility test and verify red**

Run:
`corepack pnpm exec vitest run tests/model/OllamaProvider.test.ts`

Expected: FAIL because the root provider is still a hard-coded stub.

- [ ] **Step 3: Implement the compatibility adapter**

Delegate to:

```ts
import {
  OllamaProvider as ArchitectOllamaProvider,
  type OllamaProviderOptions,
} from '@aaes-os/architect-agent';
```

Preserve the root class name and `generate(prompt)` interface. Add the
workspace dependency and aliases required by TypeScript and Vitest.

- [ ] **Step 4: Run focused and workspace verification**

Run:
`corepack pnpm exec vitest run tests/model/OllamaProvider.test.ts`

Run:
`corepack pnpm run build`

Run:
`corepack pnpm test`

Expected: all commands exit 0.

- [ ] **Step 5: Commit the adapter**

Stage only the root provider contract, adapter, test, package metadata,
configuration, and lockfile. Commit:

`feat(model): connect root provider to architect agent`

## Task 5: Restore and Configure Lawful Nova

**Files:**
- Preserve: `E:\project-infi\lawful-nova-shell`
- Restore: dedicated `agentic-coding-agent` source checkout
- Modify: local-model, provider, config, desktop, setup, and focused test files

- [ ] **Step 1: Inventory and preserve the artifact-only directory**

Resolve and print the source and backup absolute paths. Confirm both remain
under `E:\project-infi`. Rename the existing directory without deleting it.

- [ ] **Step 2: Restore the dedicated repository**

Clone:

```powershell
git clone --branch codex/nova-desktop-node-quickstart `
  https://github.com/warheart1984-ctrl/agentic-coding-agent.git `
  E:\project-infi\lawful-nova-shell
```

Verify `git -C E:\project-infi\lawful-nova-shell rev-parse --show-toplevel`
returns that directory.

- [ ] **Step 3: Run the source baseline**

Run the repository's Python tests and desktop tests before edits. Record any
pre-existing failures without masking them.

- [ ] **Step 4: Write failing model-default and payload tests**

Assert that Python local generation uses:

```python
{
    "model": "qwen2.5-coder:3b",
    "prompt": prompt,
    "stream": False,
    "options": {"temperature": 0.2, "num_predict": 2048},
}
```

Assert the provider and desktop defaults are 3B and both 3B/7B choices are
available.

- [ ] **Step 5: Run focused tests and verify red**

Run the exact Python and desktop test files containing the new assertions.
Expected: failures reference stale `phi3` or 7B defaults and missing
non-streaming options.

- [ ] **Step 6: Implement consistent configuration**

Update Python, Electron, JSON configuration, and startup scripts to use
`qwen2.5-coder:3b` by default while accepting
`qwen2.5-coder:7b` explicitly. Keep environment-variable overrides intact.

- [ ] **Step 7: Run Lawful Nova tests**

Run all Python tests, desktop tests, and repository verification scripts.
Expected: all source-controlled checks pass; unavailable optional services may
produce documented warnings only.

- [ ] **Step 8: Run a live 3B smoke test**

Confirm `ollama list` contains `qwen2.5-coder:3b`. Generate one bounded coding
proposal through the actual Lawful Nova adapter and validate its output.

- [ ] **Step 9: Commit Lawful Nova changes**

Stage only source, tests, and configuration. Scan staged content for secrets
and generated files. Commit:

`feat(models): default local coding to qwen 3b`

## Task 6: Final Readiness Audit

**Files:**
- Modify: `.github/workflows/ci.yml` only if needed
- Modify: lockfiles only through package-manager commands

- [ ] **Step 1: Verify Project Infinity**

Run `corepack pnpm install --frozen-lockfile`, full build, full tests,
`git diff --check`, and a staged-secret scan.

- [ ] **Step 2: Verify Lawful Nova**

Run full Python tests, desktop tests, Windows verification, `git diff --check`,
and a staged-secret scan.

- [ ] **Step 3: Audit Git publication boundaries**

For each repository, report top-level path, branch, remote, commits ahead of
upstream, staged files, unstaged files, and untracked files. Confirm no model
blob, virtual environment, cache, packaged binary, or unrelated user file is
included.

- [ ] **Step 4: Report push readiness**

State `ready`, `ready with scoped push`, or `not ready` separately for Project
Infinity and Lawful Nova, citing fresh command outcomes and any remaining
blocker.
