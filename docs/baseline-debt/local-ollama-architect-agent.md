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
- AAES full build and 27-test suite passed after restoring the public
  `SqliteTraceStoreStub`
- governance-genome gate passed with 199 genomes
- the four previously blocked pytest modules pass successfully (251 tests)

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

## Post-Rebase Baseline Corrections

### Standalone AAES-OS missing export: corrected

`aaes-os/src/index.ts` exports `SqliteTraceStoreStub`, while
`aaes-os/src/storage/trace_store.ts` previously defined only
`InMemoryTraceStore`.

The fail-closed v1 stub has been restored with adversarial read and write tests.
The complete standalone AAES build and test suite now pass.

### Governance-genome boot validation: corrected

Fifty-nine genome manifests contained workstation-specific absolute proof paths
under `E:\project-infi`. Those paths escaped the NTFS worktree and caused
`Alt4Runtime.boot_validate()` to raise `GenomeValidationError`.

The paths are now repository-relative, and the conformance suite asserts that
Windows and POSIX absolute proof paths are forbidden.

Previously affected collection targets:

1. `tests/otem/test_otem_stabilization.py`
2. `tests/test_api.py`
3. `tests/test_api_mechanic_slingshot.py`
4. `tests/test_api_operator_training_adapters.py`

All four modules now pass successfully. The strict genome gate reports 199
valid genomes.

## External Release Blockers

### GitHub Actions account lock: unresolved

PR #13 triggered the CoGOS Forge Gate and Documentation Baseline Gate, but
GitHub assigned no runner and executed zero steps. Each failed check contains
the annotation:

`The job was not started because your account is locked due to a billing issue.`

This is an external GitHub account state, not a repository test result. The
Buildkite check on the same PR passed.

### npm authentication: unresolved

`npm whoami` returns `ENEEDAUTH`. The
`@aaes-os/architect-agent@0.1.0` package passes `npm pack --dry-run`, but
publication requires an authenticated npm account with permission to publish
the `@aaes-os` scope.

## Filesystem Constraint

The primary `E:` workspace is formatted as exFAT. pnpm workspace installation
requires filesystem links that exFAT cannot provide. Dependency installation,
builds, and tests therefore run in the NTFS worktree:

`C:\Users\randj\.config\superpowers\worktrees\project-infi\local-ollama-architect-agent`

This filesystem constraint is independent of the four baseline test failures.

## Disposition

- Keep the historical pre-rebase failures documented as baseline debt.
- Do not modify missing fixtures or Theta governance artifacts in this feature.
- Keep the AAES export and portable genome-path corrections covered by
  conformance tests.
- Resolve the GitHub billing lock and npm authentication outside the repository.
- Do not create an Infinity release tag until repository-wide gates pass.
