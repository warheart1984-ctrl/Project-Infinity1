#!/usr/bin/env bash
# Stage Wolf CoG OS runtime + d-i hook files on ISO /install/ (outside squashfs).
set -euo pipefail

stage_di_iso_payload() {
  local rootfs="${1:-${WORK:?}/rootfs}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local iso_install="${WORK}/iso/install/wolf-cog-os"
  local preseed_src="$script_dir/../payload-iso/install/wolf-cog-os.preseed"
  local late_src="$script_dir/../payload-iso/install/cogos-di-late-command.sh"
  local stage="${WORK}/tmp/cogos-di-runtime-stage"

  [[ -d "$rootfs/opt/cogos" ]] || {
    echo "ERROR: stage_di_iso_payload: missing $rootfs/opt/cogos" >&2
    return 1
  }

  mkdir -p "$iso_install"
  cp -f "$preseed_src" "${WORK}/iso/install/wolf-cog-os.preseed"
  cp -f "$late_src" "$iso_install/cogos-di-late-command.sh"
  cp -f "$rootfs/usr/local/bin/cogos-install-finish" "$iso_install/cogos-install-finish"
  chmod +x "$iso_install/cogos-di-late-command.sh" "$iso_install/cogos-install-finish"

  rm -rf "$stage"
  mkdir -p "$stage/opt/cogos" "$stage/usr/local/bin" "$stage/etc/systemd/system" "$stage/etc/init.d"
  rsync -a "$rootfs/opt/cogos/" "$stage/opt/cogos/"
  for bin in "$rootfs"/usr/local/bin/cogos-*; do
    [[ -f "$bin" ]] || continue
    cp -a "$bin" "$stage/usr/local/bin/"
  done
  if [[ -f "$rootfs/etc/init.d/90cogos" ]]; then
    cp -a "$rootfs/etc/init.d/90cogos" "$stage/etc/init.d/90cogos"
    chmod +x "$stage/etc/init.d/90cogos"
  fi
  for unit in cogos-first-boot.service cogos-runtime.service; do
    if [[ -f "$rootfs/etc/systemd/system/$unit" ]]; then
      cp -a "$rootfs/etc/systemd/system/$unit" "$stage/etc/systemd/system/$unit"
    elif [[ -f "$script_dir/../payload/etc/systemd/system/$unit" ]]; then
      cp -a "$script_dir/../payload/etc/systemd/system/$unit" "$stage/etc/systemd/system/$unit"
    fi
  done
  if [[ ! -f "$stage/etc/init.d/90cogos" && -f "$script_dir/../payload/etc/init.d/90cogos" ]]; then
    cp -a "$script_dir/../payload/etc/init.d/90cogos" "$stage/etc/init.d/90cogos"
    chmod +x "$stage/etc/init.d/90cogos"
  fi

  local wrapper_count=0
  wrapper_count="$(find "$stage/usr/local/bin" -maxdepth 1 -name 'cogos-*' -type f | wc -l)"
  [[ -x "$stage/etc/init.d/90cogos" ]] || {
    echo "ERROR: stage_di_iso_payload: 90cogos missing from runtime.tar stage" >&2
    return 1
  }
  [[ -f "$stage/etc/systemd/system/cogos-runtime.service" ]] || {
    echo "ERROR: stage_di_iso_payload: cogos-runtime.service missing from runtime.tar stage" >&2
    return 1
  }
  if [[ "$wrapper_count" -lt 40 ]]; then
    echo "ERROR: stage_di_iso_payload: only $wrapper_count cogos-* wrappers staged (need >= 40)" >&2
    return 1
  fi

  tar -C "$stage" -cf "$iso_install/runtime.tar" .
  rm -rf "$stage"

  echo "[4d/9] Debian installer payload on ISO: runtime.tar ($(du -h "$iso_install/runtime.tar" | awk '{print $1}'), $wrapper_count wrappers, 90cogos + cogos-runtime.service)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  WORK="${COGOS_WORK:?}"
  # shellcheck source=paths.sh
  source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/paths.sh"
  stage_di_iso_payload "${1:-$WORK/rootfs}"
fi
