#!/usr/bin/env bash
# Unbrick a d-i install: restore native systemd PID1 + enable cogos-runtime.service.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash fix-bricked-di-install.sh /dev/sdXN"
  exit 1
fi

DEV="$1"
MNT="${MNT:-/mnt/cogos-fix}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! mountpoint -q "$MNT"; then
  mkdir -p "$MNT"
  mount "$DEV" "$MNT"
fi

echo "Unbricking Wolf CoG OS install on $MNT ..."

# Restore native systemd as PID1
rm -f "$MNT/usr/sbin/init" "$MNT/sbin/init"
ln -sf /lib/systemd/systemd "$MNT/usr/sbin/init"
if [[ -d "$MNT/sbin" ]]; then
  ln -sf /lib/systemd/systemd "$MNT/sbin/init"
fi
echo "  PID1 -> /lib/systemd/systemd"

# Overlay fixed payload bits from repo
PAYLOAD="$SCRIPT_DIR/../payload"
for f in \
  usr/local/bin/cogos-install-finish \
  usr/local/bin/cogos-runtime-start \
  usr/local/bin/cogos-runtime-stop \
  etc/systemd/system/cogos-runtime.service \
  etc/init.d/90cogos; do
  if [[ -f "$PAYLOAD/$f" ]]; then
    install -D -m755 "$PAYLOAD/$f" "$MNT/$f" 2>/dev/null || install -D -m644 "$PAYLOAD/$f" "$MNT/$f"
    echo "  installed $f"
  fi
done

# Remove broken SysV enable symlinks if any
rm -f "$MNT/etc/rc2.d/S90cogos" "$MNT/etc/rc3.d/S90cogos" \
      "$MNT/etc/rc4.d/S90cogos" "$MNT/etc/rc5.d/S90cogos" 2>/dev/null || true

if [[ -x "$MNT/usr/local/bin/cogos-install-finish" ]]; then
  chroot "$MNT" /usr/local/bin/cogos-install-finish --in-target --keep-systemd-pid1 --quiet
fi

if chroot "$MNT" command -v update-initramfs >/dev/null 2>&1; then
  chroot "$MNT" update-initramfs -u -k all || true
fi
if chroot "$MNT" command -v update-grub >/dev/null 2>&1; then
  chroot "$MNT" update-grub || true
fi

echo "Done. Reboot from internal disk (remove USB)."
echo "Then: systemctl status cogos-runtime.service"
