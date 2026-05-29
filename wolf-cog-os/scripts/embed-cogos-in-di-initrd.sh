#!/usr/bin/env bash
# Embed CoGOS payload + preseed + late hook into Debian gtk/text installer initrd images.
set -euo pipefail

embed_cogos_in_di_initrd() {
  local runtime_tar="${1:-${WORK:?}/iso/install/wolf-cog-os/runtime.tar}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local extra="${WORK}/tmp/cogos-di-initrd-extra"
  local late_src="$script_dir/../payload-iso/install/cogos-di-late-command.sh"
  local preseed_src="$script_dir/../payload-iso/install/preseed.cfg"
  local finish_src="${WORK}/rootfs/usr/local/bin/cogos-install-finish"

  [[ -f "$runtime_tar" ]] || {
    echo "ERROR: embed_cogos_in_di_initrd: missing $runtime_tar (run stage_di_iso_payload first)" >&2
    return 1
  }

  rm -rf "$extra"
  mkdir -p "$extra/cogos-hooks" "$extra/cogos-payload"
  gzip -9 -c "$runtime_tar" > "$extra/cogos-payload/runtime.tar.gz"
  cp -f "$late_src" "$extra/cogos-hooks/cogos-di-late-command.sh"
  cp -f "$preseed_src" "$extra/preseed.cfg"
  if [[ -f "$finish_src" ]]; then
    cp -f "$finish_src" "$extra/cogos-hooks/cogos-install-finish"
    chmod +x "$extra/cogos-hooks/cogos-install-finish"
  fi
  chmod +x "$extra/cogos-hooks/cogos-di-late-command.sh"

  local patched=0
  for initrd in \
    "${WORK}/iso/install/gtk/initrd.gz" \
    "${WORK}/iso/install/initrd.gz"; do
    [[ -f "$initrd" ]] || continue
    _append_cpio_to_initrd "$initrd" "$extra" || continue
    patched=$((patched + 1))
    echo "[4e/9] CoGOS embedded in $(basename "$(dirname "$initrd")")/initrd.gz (+$(du -h "$initrd" | awk '{print $1}'))"
  done

  if (( patched == 0 )); then
    echo "ERROR: no gtk/text initrd.gz found under $WORK/iso/install/" >&2
    return 1
  fi
  echo "[4e/9] d-i initrd embed complete ($patched initrd images)"
}

_append_cpio_to_initrd() {
  local initrd_gz="$1"
  local extra_dir="$2"
  local tmp="${WORK}/tmp/initrd-append-$$"
  local raw="$tmp/initrd.raw"
  local backup="${initrd_gz}.orig"

  mkdir -p "$tmp"
  if [[ ! -f "$backup" ]]; then
    cp -a "$initrd_gz" "$backup"
  fi

  gzip -dc "$backup" > "$raw"
  (
    cd "$extra_dir"
    find . -print0 | cpio --null -o -H newc --quiet >> "$raw"
  )
  gzip -9 -c "$raw" > "$initrd_gz"
  rm -rf "$tmp"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  WORK="${COGOS_WORK:?}"
  embed_cogos_in_di_initrd "${1:-}"
fi
