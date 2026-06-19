#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
export LAWFUL_NOVA_REPO_ROOT="$REPO_ROOT"
export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:$PYTHONPATH}"
"$REPO_ROOT/scripts/nova-bootstrap-lsg.sh"
if (($#)); then
  exec python -m nova "$@"
else
  exec python -m nova health
fi
