#!/usr/bin/env bash
# Repair CoGOS daemons on an already-installed disk (boot live USB, run against root partition).
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash fix-installed-daemons.sh /dev/sdXN"
  echo "  Mounts ext4 root, installs missing daemon launcher + enables cogos-runtime.service"
  exit 1
fi

DEV="$1"
MNT="${MNT:-/mnt/cogos-fix}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$SCRIPT_DIR/../payload"

if ! mountpoint -q "$MNT"; then
  mkdir -p "$MNT"
  mount "$DEV" "$MNT"
fi

echo "Repairing CoGOS daemons on $MNT ..."

# Install init.d launcher + systemd unit if missing
if [[ -f "$PAYLOAD/etc/init.d/90cogos" ]]; then
  install -D -m755 "$PAYLOAD/etc/init.d/90cogos" "$MNT/etc/init.d/90cogos"
fi
if [[ -f "$PAYLOAD/etc/systemd/system/cogos-runtime.service" ]]; then
  install -D -m644 "$PAYLOAD/etc/systemd/system/cogos-runtime.service" \
    "$MNT/etc/systemd/system/cogos-runtime.service"
fi

# Copy any missing cogos-* wrappers from payload cache / repo merged rootfs
if [[ -d "$PAYLOAD/usr/local/bin" ]]; then
  mkdir -p "$MNT/usr/local/bin"
  for bin in "$PAYLOAD"/usr/local/bin/cogos-*; do
    [[ -f "$bin" ]] || continue
    name="$(basename "$bin")"
    [[ -x "$MNT/usr/local/bin/$name" ]] && continue
    install -m755 "$bin" "$MNT/usr/local/bin/$name"
    echo "  installed $name"
  done
fi

# Re-run install finish to enable units + daily driver profile
if [[ -x "$MNT/usr/local/bin/cogos-install-finish" ]]; then
  chroot "$MNT" /usr/local/bin/cogos-install-finish --in-target
else
  mkdir -p "$MNT/etc/systemd/system/multi-user.target.wants"
  ln -sf ../cogos-runtime.service "$MNT/etc/systemd/system/multi-user.target.wants/cogos-runtime.service"
  chroot "$MNT" update-rc.d 90cogos defaults 2>/dev/null || true
fi

echo "Done. Reboot from internal disk."
echo "After boot: systemctl status cogos-runtime.service"
echo "Logs: /var/log/cogos-service.log /var/log/cogos-first-boot.log"
