#!/usr/bin/env bash
# Fedora/openSUSE LiveOS replay adapter (P10).
set -euo pipefail

adapter_resolve_sfs() {
  local work_iso="$1"
  local candidate
  SFS_SOURCE=""
  for candidate in \
    "$work_iso/LiveOS/squashfs.img" \
    "$work_iso/LiveOS/ext3fs.img" \
    "$(find "$work_iso/LiveOS" -maxdepth 1 -type f 2>/dev/null | head -n 1)"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      SFS_SOURCE="$candidate"
      break
    fi
  done
  SFS_NAME="$(basename "${SFS_SOURCE:-squashfs.img}")"
}

adapter_sfs_write_path() {
  local work_iso="$1"
  if [[ -n "${SFS_SOURCE:-}" ]]; then
    printf '%s\n' "$SFS_SOURCE"
    return 0
  fi
  printf '%s\n' "$work_iso/LiveOS/squashfs.img"
}

adapter_workdir_ready() {
  local work="$1"
  adapter_resolve_sfs "$work/iso"
  [[ -n "${SFS_SOURCE:-}" && -f "$SFS_SOURCE" ]] || return 1
  [[ -f "$work/rootfs/etc/os-release" ]] || return 1
}

adapter_extract_rootfs() {
  local _work_iso="$1"
  local rootfs_out="$2"
  if [[ -z "${SFS_SOURCE:-}" ]]; then
    echo "ERROR: fedora-liveos-layout: no LiveOS squashfs image found" >&2
    return 4
  fi
  if [[ "${COGOS_XATTRS:-0}" == "1" ]]; then
    unsquashfs -f -d "$rootfs_out" "$SFS_SOURCE"
  else
    unsquashfs -no-xattrs -f -d "$rootfs_out" "$SFS_SOURCE"
  fi
}
