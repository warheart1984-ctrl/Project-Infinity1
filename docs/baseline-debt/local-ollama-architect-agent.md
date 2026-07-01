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

## Filesystem Constraint

The primary `E:` workspace is formatted as exFAT. pnpm workspace installation
requires filesystem links that exFAT cannot provide. Dependency installation,
builds, and tests therefore run in the NTFS worktree:

`C:\Users\randj\.config\superpowers\worktrees\project-infi\local-ollama-architect-agent`

This filesystem constraint is independent of the four baseline test failures.

## Disposition

- Keep the failures documented as baseline debt.
- Do not modify missing fixtures or Theta governance artifacts in this feature.
- Rebase only architect-agent commits onto current `origin/main`.
- Re-run the full matrix in the NTFS worktree.
- Update this report with post-rebase evidence before publication.
