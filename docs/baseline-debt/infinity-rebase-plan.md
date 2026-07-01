# Infinity Architect-Agent Rebase Plan

## Objective

Move only the local Ollama architect-agent work onto current `origin/main`
without carrying unrelated AAES production-sweep commits or repairing baseline
debt during the rebase.

## Included Commits

- `ae371bb7` - design specification
- `29db9e12` - implementation plan
- `4788d56a` - governed architect-agent package
- `efdee491` - root provider compatibility adapter
- baseline-debt documentation commit

## Excluded Commits

The older AAES production-sweep and Theta-profile commits preceding
`4520a1e7` remain outside this feature branch.

## Executed Procedure

1. Fetch and prune `origin`.
2. Confirm the NTFS worktree is clean.
3. Rebase commits after `4520a1e7` onto `origin/main`.
4. Resolve conflicts only for architect-agent-owned files.
5. Adapt the compatibility layer to the standalone `aaes-os/` runtime that
   replaced the old root pnpm workspace on current main.
6. Run `npm ci` in `packages/architect-agent` and `aaes-os`.
7. Run the architect-agent and AAES compatibility-adapter tests.
8. Run the standalone AAES build and full root pytest collection.
9. Record the post-rebase pass/failure counts in the debt report.
10. Run whitespace and credential-pattern scans.
11. Push only after the feature checks remain green and all residual failures
    are identified as baseline debt.

## Rebase Outcome

- Rebased successfully onto `origin/main` commit `6280e45a`.
- Dropped the unrelated AAES production-sweep and Theta commits.
- Kept the standalone architect-agent package.
- Moved the compatibility adapter from the deleted root TypeScript workspace
  to `aaes-os/src/model`.
- Added a targeted `aaes-os` model test that does not depend on the unrelated
  full-runtime compile path.
- Recorded the new main-branch baseline blockers in the debt report.

## Publication Gate

The branch may be published for review when:

- the architect-agent package tests pass,
- the root adapter test passes,
- the workspace build passes,
- live 3B generation succeeds,
- no new repository-wide failure appears,
- residual failures are documented rather than silently ignored.

An Infinity release tag remains blocked until repository-wide CI is green.
