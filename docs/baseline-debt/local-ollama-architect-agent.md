# Project Infinity Baseline Debt Report

## Scope

This report records repository-wide failures observed before and after the
local Ollama architect-agent implementation. The feature-specific package,
adapter, build, and live-model checks pass independently.

Baseline command:

```powershell
corepack pnpm test
```

Pre-rebase result at commit `efdee491`:

- 149 tests passed
- 4 tests failed
- all 22 package and service builds passed

Post-rebase base commit:

`6280e45a` (`origin/main`)

Current feature results:

- architect-agent: 28 tests passed
- AAES compatibility adapter: 1 test passed
- architect-agent TypeScript build passed
- AAES full build blocked by one pre-existing missing export
- root pytest collection blocked by four pre-existing governance-genome boot
  validation errors

The old pnpm workspace and its four failures described below are no longer
present on current `origin/main`. They remain recorded as historical
pre-rebase evidence.

## Baseline Failures

### Missing recent-document coverage fixture

Missing path:

`docs/coverage/recent-doc-subsystem-coverage.json`

Affected tests:

1. `tests/integration/recent-doc-coverage.test.ts`
2. `services/ops-console/src/server.test.ts`

The integration test cannot read the expected JSON file. The ops-console
coverage route consequently returns HTTP 400 instead of 200.

### Missing coordination fixture

Missing path:

`tests/fixtures/coordination_bottlenecks.md`

Affected test:

`packages/governed-memory/src/verticalSlice.test.ts`

The replay test fails before runtime evaluation because its fixture cannot be
opened.

### Theta profile manifest hash drift

Affected test:

`packages/theta-codec/src/thetaCodec.test.ts`

The governed artifact records:

`fac9cef137bbd2a7ab6b2d439bb3ecdc32bc8be678cebbfc2f523b68b364f5b0`

The current manifest computes:

`9b07c2189c7a52642ff48f06ca127709302a914939aef251243e01d5830e6a01`

Updating either the governed hash or the manifest requires a separate
Theta-profile review and is outside the architect-agent feature.

## Feature Verification

The following checks pass:

- `@aaes-os/architect-agent`: 28 tests
- root Ollama compatibility adapter: 1 test
- recursive workspace build: all 22 package and service projects
- live `qwen2.5-coder:3b` proposal generation
- feature diff whitespace scan
- feature diff credential-pattern scan

No baseline failure is in an architect-agent file.

## Post-Rebase Baseline Failures

### Standalone AAES-OS missing export

`aaes-os/src/index.ts` exports `SqliteTraceStoreStub`, while
`aaes-os/src/storage/trace_store.ts` defines only `InMemoryTraceStore`.

This defect exists on `origin/main` and stops the full standalone AAES
TypeScript build. The architect-agent package build and targeted compatibility
test pass independently.

### Governance-genome boot validation

Full root pytest collection stops while importing `src.api` because
`Alt4Runtime.boot_validate()` raises `GenomeValidationError`.

Affected collection targets:

1. `tests/otem/test_otem_stabilization.py`
2. `tests/test_api.py`
3. `tests/test_api_mechanic_slingshot.py`
4. `tests/test_api_operator_training_adapters.py`

No architect-agent TypeScript module is imported by these tests.

### GitHub Actions account lock

PR #13 triggered the CoGOS Forge Gate and Documentation Baseline Gate, but
GitHub assigned no runner and executed zero steps. Each failed check contains
the annotation:

`The job was not started because your account is locked due to a billing issue.`

This is an external GitHub account state, not a repository test result. The
Buildkite check on the same PR passed.

## Filesystem Constraint

The primary `E:` workspace is formatted as exFAT. pnpm workspace installation
requires filesystem links that exFAT cannot provide. Dependency installation,
builds, and tests therefore run in the NTFS worktree:

`C:\Users\randj\.config\superpowers\worktrees\project-infi\local-ollama-architect-agent`

This filesystem constraint is independent of the four baseline test failures.

## Disposition

- Keep the failures documented as baseline debt.
- Do not modify missing fixtures or Theta governance artifacts in this feature.
- Do not modify the missing AAES export or governance-genome registry in this
  feature.
- Publish the rebased architect-agent branch for review with the baseline
  failures disclosed.
- Do not create an Infinity release tag until repository-wide gates pass.
