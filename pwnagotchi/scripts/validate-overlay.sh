#!/usr/bin/env bash
set -eu -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

required=(
  config/config.toml.example
  config/NetworkManager/90-pwnagotchi-dns.conf
  config/NetworkManager/90-pwnagotchi-wifi-unmanaged.conf
  systemd/bettercap.service.d/10-networkmanager-order.conf
  systemd/bettercap.service.d/20-safe-launcher.conf
  systemd/bettercap.service.d/30-restart-limit.conf
  systemd/pwnagotchi.service.d/10-bettercap-readiness.conf
  systemd/pwnagotchi.service.d/15-pwngrid-readiness.conf
  systemd/pwngrid-peer.service.d/10-bettercap-readiness.conf
  overlay-bin/bettercap-launcher-safe
  overlay-bin/pwnagotchi-wait-bettercap
  overlay-bin/pwnagotchi-wait-pwngrid
  overlay-bin/pwnagotchi-launcher
  upstream/modified-plugins/wpa-sec.py
  upstream/modified-plugins/wigle.py
)

for rel in "${required[@]}"; do
    test -f "$ROOT/$rel" || {
        echo "FAIL: missing $rel" >&2
        exit 1
    }
done

for script in "$ROOT"/overlay-bin/* "$ROOT"/scripts/*.sh; do
    bash -n "$script"
done

python3 -m py_compile \
    "$ROOT/upstream/modified-plugins/wpa-sec.py" \
    "$ROOT/upstream/modified-plugins/wigle.py"

rm -rf "$ROOT/upstream/modified-plugins/__pycache__"

"$ROOT/scripts/check-publication.sh"

echo 'PASS: Pwnagotchi overlay tree validated'
