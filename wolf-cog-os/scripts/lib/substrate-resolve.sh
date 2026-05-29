#!/usr/bin/env bash
# Resolve OS-agnostic Forge replay substrate ISO paths.
set -euo pipefail

substrate_registry_path() {
  echo "${COGOS_SUBSTRATE_REGISTRY:-wolf-cog-os/forge/substrates/registry.json}"
}

# Canonical: COGOS_SUBSTRATE_ISO
# Aliases: COGOS_BOOT_REPLAY_ISO, COGOS_DEBIAN_ISO (legacy)
substrate_resolve_iso_path() {
  local cli_iso="${1:-}"
  if [[ -n "$cli_iso" && -f "$cli_iso" ]]; then
    printf '%s\n' "$(readlink -f "$cli_iso" 2>/dev/null || echo "$cli_iso")"
    return 0
  fi
  if [[ -n "${COGOS_SUBSTRATE_ISO:-}" && -f "${COGOS_SUBSTRATE_ISO}" ]]; then
    printf '%s\n' "$(readlink -f "$COGOS_SUBSTRATE_ISO")"
    return 0
  fi
  if [[ -n "${COGOS_BOOT_REPLAY_ISO:-}" && -f "${COGOS_BOOT_REPLAY_ISO}" ]]; then
    printf '%s\n' "$(readlink -f "$COGOS_BOOT_REPLAY_ISO")"
    return 0
  fi
  if [[ -n "${COGOS_DEBIAN_ISO:-}" && -f "${COGOS_DEBIAN_ISO}" ]]; then
    printf '%s\n' "$(readlink -f "$COGOS_DEBIAN_ISO")"
    return 0
  fi
  if [[ -n "${DEBIAN_BASE_ISO:-}" && -f "${DEBIAN_BASE_ISO}" ]]; then
    printf '%s\n' "$(readlink -f "$DEBIAN_BASE_ISO")"
    return 0
  fi
  return 1
}

substrate_export_env() {
  local iso_path="$1"
  export COGOS_SUBSTRATE_ISO="$iso_path"
  export COGOS_BOOT_REPLAY_ISO="$iso_path"
  export COGOS_DEBIAN_ISO="$iso_path"
}

substrate_validate() {
  local iso_path="$1"
  local substrate_id="${2:-auto}"
  local mode="${3:-fail}"
  local output="${4:-ci-artifacts/substrate-validation.json}"
  python3 "$REPO_ROOT/wolf-cog-os/scripts/validate-substrate.py" \
    --iso "$iso_path" \
    --substrate-id "$substrate_id" \
    --registry "$(substrate_registry_path)" \
    --mode "$mode" \
    --output "$output"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  _dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  # shellcheck source=paths.sh
  source "$_dir/paths.sh"
  resolved="$(substrate_resolve_iso_path "${1:-}")" || {
    echo "ERROR: no substrate ISO resolved; set COGOS_SUBSTRATE_ISO or pass path" >&2
    exit 2
  }
  substrate_id="${COGOS_SUBSTRATE_ID:-auto}"
  substrate_validate "$resolved" "$substrate_id" "${COGOS_SUBSTRATE_VALIDATION_MODE:-fail}"
fi
