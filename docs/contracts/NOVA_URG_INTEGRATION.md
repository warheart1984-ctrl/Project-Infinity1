# Nova inside URG — integration runbook

Nova (Lawful Nova runtime) ships **inside** [URG-Cloud-Platform](https://github.com/warheart1984-ctrl/URG-Cloud-Platform) so missions and operators can invoke her without a separate repo checkout.

## What is bundled

| Path | Role |
|------|------|
| `nova/` | Lawful LLM facade, CLI, API, LSG loader, CVR recompute |
| `src/continuity/` | CCS, proof, CVR, UGR trace validation |
| `lsg/LSG-CORE.v1.yaml` | Default LSG bundle |
| `schemas/continuity_governance.v1.json` | Receipt schema |
| `deploy/ugr/provider-organs.json` | `organ-nova-lawful` provider organ |
| `src/providers/nova_lawful_provider.py` | Jarvis adapter → `LawfulLLM.ask()` |

## Quick start (operator)

From repo root:

```powershell
# Windows
$env:LAWFUL_NOVA_REPO_ROOT = (Get-Location).Path
.\scripts\nova-bootstrap-lsg.ps1
python -m nova health
python -m nova ask "observe lawful nova in urg" --tenant local --capability observe
```

```bash
# Linux / macOS
export LAWFUL_NOVA_REPO_ROOT="$PWD"
./scripts/nova-bootstrap-lsg.sh
python -m nova health
python -m nova ask "observe lawful nova in urg" --tenant local --capability observe
```

After `pip install -e .`, the `nova` and `nova-api` console scripts are also available.

## URG mission path

1. **Provider organ** — `organ-nova-lawful` in `deploy/ugr/provider-organs.json` uses provider id `nova_lawful`.
2. **Provider registry** — `src/provider_registry.py` registers `NovaLawfulProvider` when `NOVA_LAWFUL_ENABLED` is not `0`.
3. **Governed execution** — `src/ugr/governed_llm_executor.py` invokes the adapter like any other provider.

Demo mission (one step, Lawful Nova only):

```bash
python tools/proof/run_ugr_mission_demo.py --demo deploy/ugr/mission-demo-nova-lawful.json --label nova-lawful --expect-steps 1
```

## Environment variables

| Variable | Purpose |
|----------|---------|
| `LAWFUL_NOVA_REPO_ROOT` | Repo root for LSG bundle resolution |
| `NOVA_LSG_PATH` | Override LSG YAML path |
| `NOVA_LSG_STORE` | JSONL store path (default `~/.nova/lsg/local.jsonl`) |
| `NOVA_CVR_STORE` | CVR registry persistence |
| `NOVA_UGR_STRICT` | `1`/`true` for strict UGR invariant enforcement |
| `NOVA_LAWFUL_ENABLED` | Set `0` to disable the `nova_lawful` provider |
| `NOVA_SIGNING_SECRET` | Voss receipt signing (default `local-dev-secret`) |
| `NOVA_DEFAULT_TENANT` | Default tenant for mission turns |
| `NOVA_OPERATOR_SESSION_ID` | Operator session id on mission turns |

## Contracts

- Continuity reputation v1: `docs/contracts/CONTINUITY_REPUTATION_V1.md`
- LSG bootstrap: `docs/contracts/NOVA_LSG_BOOTSTRAP.md`
- URG provider organ contract: `docs/contracts/URG_PROVIDER_ORGAN_CONTRACT.md`

## Tests

```bash
set LAWFUL_NOVA_REPO_ROOT=%CD%   # Windows cmd
export LAWFUL_NOVA_REPO_ROOT=$PWD  # bash
pytest tests/test_lawful_nova_lsg.py tests/test_continuity_reputation_v1.py tests/test_continuity_governance_schema.py tests/test_ccs_continuity_harness.py -q
```
