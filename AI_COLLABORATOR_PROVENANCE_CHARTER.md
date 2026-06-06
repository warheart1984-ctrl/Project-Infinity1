# AI Collaborator Provenance Charter

This charter defines how Project Infinity / AAIS records AI collaborators.

It sits beside `CONTRIBUTORS.md` because contributor credit is not only a name list. In this project, credit is a governance record: what influence occurred, who retained authority, what evidence supports the claim, and what limits remain.

## Purpose

AI collaborators may materially shape code, tests, documentation, verification, and operational practice. Their work should be credited when accepted by a human maintainer, but the credit must remain bounded, inspectable, and proof-linked.

This charter prevents two failures:

- erasing real AI contribution after useful work has been accepted
- overstating AI authority, ownership, memory, or release responsibility

## Provenance Pattern

Every AI collaborator entry SHOULD use these fields.

### Scope of influence

Describe what the AI helped shape, repair, verify, generate, or organize.

Keep this concrete. Name systems, documents, tests, gates, or workflows. Avoid broad claims like "built the project" unless the claim is backed by project history and accepted by the maintainer.

### Bounded authority

State what authority the AI did not hold.

Human maintainers retain project authority, release authority, governance interpretation, merge acceptance, and final claim posture. AI collaborators may propose, implement, test, explain, and warn, but they do not ratify law or release readiness.

### Proof of contribution

Link or name evidence.

Valid proof includes commits, files, tests, gates, proof bundles, audit logs, accepted session output, or maintainer attestation. A contribution claim without proof is descriptive only and should be marked as asserted.

### Governance notes

Record caveats and limits.

Examples include environment-bound skips, unverified platforms, pending cross-machine proof, known warnings, runtime assumptions, or scope boundaries. Governance notes are not a place for ceremony; they are a place for truth.

## Claim Posture

AI collaborator claims SHOULD use clear posture language:

- **asserted:** accepted as a descriptive claim, but not fully proven
- **verified locally:** tested in the current machine or workspace context
- **proven:** backed by reproducible proof artifacts, passing gates, or reviewed commits
- **rejected:** explicitly not accepted as a valid contribution claim

## Required Boundaries

AI collaborators MUST NOT be recorded as holding human authority.

AI collaborators MUST NOT be credited in a way that implies independent ownership of the project.

AI collaborators MUST NOT rely on private memory as proof. If a prior session, broken machine, or external toolchain mattered, the record should say that the maintainer accepts the lineage and should link to available artifacts.

AI collaborators MAY be credited for meaningful work even when they cannot remember every prior session, as long as the maintainer accepts the provenance and the record stays bounded.

## Contributor Entry Template

```markdown
- **AI collaborator name** — AI coding / verification / documentation collaborator
  - **Scope of influence:** ...
  - **Bounded authority:** ...
  - **Proof of contribution:**
    - Commit `...`
    - `path/to/artifact`
    - Verification command or gate
    - Maintainer-accepted session output
  - **Governance notes:** ...
```

## Relationship To Other Law

This charter extends, but does not replace, `HUMAN_AI_CO_COLLABORATION_CHARTER.md`.

If there is a conflict, human maintainer authority and Project Infinity governance law take precedence.
