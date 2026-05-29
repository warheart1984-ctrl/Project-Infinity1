#!/usr/bin/env bash
# Pre-release gate: full-runtime payload must install and first-boot cleanly.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

PAYLOAD="${COGOS_PAYLOAD:-${COGOS_PAYLOAD_CACHE:-${HOME}/.cogos-payload-cache}}"
if [[ ! -d "$PAYLOAD/opt/cogos" ]]; then
  PAYLOAD="${COGOS_PAYLOAD:-$WOLF_PAYLOAD}"
fi
FAIL=0

check() {
  if eval "$2"; then
    echo "OK  $1"
  else
    echo "FAIL $1" >&2
    FAIL=1
  fi
}

echo "=== Full runtime release payload verify ==="
echo "Payload: $PAYLOAD"
echo ""

check "cogos-install" "test -x '$PAYLOAD/usr/local/bin/cogos-install'"
check "cogos-install-finish" "test -x '$PAYLOAD/usr/local/bin/cogos-install-finish'"
check "cogos-first-boot" "test -x '$PAYLOAD/usr/local/bin/cogos-first-boot'"
check "cognitive_init" "test -x '$PAYLOAD/opt/cogos/bin/cognitive_init'"
check "first-boot fast handoff in cognitive_init" \
  "grep -q first_boot_fast_handoff '$PAYLOAD/opt/cogos/bin/cognitive_init'"
check "first-boot service after graphical.target" \
  "grep -q 'WantedBy=graphical.target' '$PAYLOAD/etc/systemd/system/cogos-first-boot.service'"
check "cogos-daemon wrapper" "test -x '$PAYLOAD/usr/local/bin/cogos-daemon'"
check "cogos-runtime-start" "test -x '$PAYLOAD/usr/local/bin/cogos-runtime-start'"
check "cogos-runtime.service native ExecStart" "grep -q 'cogos-runtime-start' '$PAYLOAD/etc/systemd/system/cogos-runtime.service'"
check "90cogos daemon launcher" "test -x '$PAYLOAD/etc/init.d/90cogos'"
check "cogos-runtime.service" "test -f '$PAYLOAD/etc/systemd/system/cogos-runtime.service'"
WRAPPER_COUNT="$(find "$PAYLOAD/usr/local/bin" -maxdepth 1 -name 'cogos-*' -type f 2>/dev/null | wc -l)"
RUNTIME_PY_COUNT="$(find "$PAYLOAD/opt/cogos/runtime" -name '*.py' 2>/dev/null | wc -l)"
check "payload wrapper count >= 40" "test '$WRAPPER_COUNT' -ge 40"
check "runtime python modules >= 50" "test '$RUNTIME_PY_COUNT' -ge 50"
check "no boot block Before=multi-user.target" \
  "! grep -q 'Before=multi-user.target' '$PAYLOAD/etc/systemd/system/cogos-first-boot.service'"

if (( FAIL )); then
  echo "" >&2
  echo "Full runtime payload checks FAILED. Sync payload from cache or rebuild." >&2
  exit 1
fi

echo ""
echo "=== All full runtime release checks passed ==="
