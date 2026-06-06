# Contributors

This file records people and agents who contributed material work to Project Infinity / AAIS.
Claims here are descriptive, not proof of release readiness — see `REPO_PROOF_LAW.md`.

## Maintainers

- **Jon Halstead** — project authority, constitutional governance, primary human operator
  - GitHub: [@warheart1984-ctrl](https://github.com/warheart1984-ctrl)

## Contributors

### Human

- **Jon Halstead** — architecture, governance lawbook, operator direction, review authority

### AI collaborators

Per [`HUMAN_AI_CO_COLLABORATION_CHARTER.md`](HUMAN_AI_CO_COLLABORATION_CHARTER.md), AI agents may be credited for
implementation work when a human maintainer accepts the contribution.

**AI collaborator provenance pattern**

Each AI collaborator entry should record:

- **Scope of influence:** what the AI helped shape or verify
- **Bounded authority:** what remained under human authority and review
- **Proof of contribution:** commits, artifacts, tests, gates, or accepted session output
- **Governance notes:** caveats, limits, skip reasons, or claim posture

- **Cursor Agent (Auto)** — AI implementation collaborator (Cursor IDE)
  - **Scope:** UL/CISIV phased rollout (Phases 1–5), chat-turn and forge/repo governance modules, CISIV
    consolidation, UL smoke fixtures, proof/trust bundles, operational README
  - **Key artifacts:**
    - `src/chat_turn_governance.py`
    - `src/forge_repo_governance.py`
    - `docs/proof/aais-ul/UL_CISIV_PHASES_1_5_PROOF.md`
    - `docs/trust_bundles/UL_CISIV_PHASES_1_5_TRUST_BUNDLE.md`
  - **Evidence:** commits `7b4e806`, `b086b1e` (2026-05-29); human-directed session with Jon Halstead
  - **Claim posture:** implementation **proven** on single-machine pytest/drift/smoke; cross-machine matrix **asserted pending**

- **OpenAI Codex** — AI coding and verification collaborator
  - **Scope of influence:** flagship verification sweeps, README presentation update, local tooling/runtime setup,
    targeted verification blocker repairs, and contributor provenance structure
  - **Bounded authority:** Codex acted as an implementation and verification collaborator only; Jon Halstead retained
    project authority, release authority, governance interpretation, and final acceptance of claims
  - **Proof of contribution:**
    - Commit `777f292`
    - `README.md`
    - `docs/assets/project-infinity-flagship.png`
    - `.github/scripts/check-lab-governance.py`
    - `src/jarvis_modular2.py`
    - Human-directed Codex session with Jon Halstead
    - Local verification: Python/backend shard sweep, frontend tests/build/lint, compile checks, dependency checks,
      and governance gates
  - **Governance notes:** implementation **verified** locally; environment-bound skips and the Windows Lab worktree
    MAX_PATH limitation were documented in session output

---

To add a contributor: open a PR that updates this file with name, scope, and linked proof artifacts.
