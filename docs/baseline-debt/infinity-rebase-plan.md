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

## Procedure

1. Fetch and prune `origin`.
2. Confirm the NTFS worktree is clean.
3. Rebase commits after `4520a1e7` onto `origin/main`.
4. Resolve conflicts only for architect-agent-owned files.
5. Run `corepack pnpm install --frozen-lockfile`.
6. Run the architect-agent and root-adapter tests.
7. Run the recursive workspace build.
8. Run `corepack pnpm test`.
9. Record the post-rebase pass/failure counts in the debt report.
10. Run whitespace and credential-pattern scans.
11. Push only after the feature checks remain green and all residual failures
    are identified as baseline debt.

## Publication Gate

The branch may be published for review when:

- the architect-agent package tests pass,
- the root adapter test passes,
- the workspace build passes,
- live 3B generation succeeds,
- no new repository-wide failure appears,
- residual failures are documented rather than silently ignored.

An Infinity release tag remains blocked until repository-wide CI is green.
